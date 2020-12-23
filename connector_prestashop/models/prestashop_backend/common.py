# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager

from odoo import models, fields, api, exceptions, _

from odoo.addons.connector.connector import ConnectorEnvironment
from ...unit.importer import import_batch, import_record
from ...unit.auto_matching_importer import AutoMatchingImporter
from ...unit.backend_adapter import GenericAdapter, api_handle_errors
from ...unit.version_key import VersionKey
from ...backend import prestashop

from ..product_template.exporter import export_product_quantities
from ..product_template.importer import import_inventory
from ..res_partner.importer import import_customers_since
from ..delivery_carrier.importer import import_carriers
from ..product_supplierinfo.importer import import_suppliers
from ..account_invoice.importer import import_refunds
from ..product_template.importer import import_products
from ..sale_order.importer import import_orders_since


_logger = logging.getLogger(__name__)


class PrestashopBackend(models.Model):
    _name = 'prestashop.backend'
    _description = 'PrestaShop Backend Configuration'
    _inherit = 'connector.backend'

    _backend_type = 'prestashop'

    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [
            ('1.5', '< 1.6.0.9'),
            ('1.6.0.9', '1.6.0.9 - 1.6.0.10'),
            ('1.6.0.11', '>= 1.6.0.11 - <1.6.1.2'),
            ('1.6.1.2', '=1.6.1.2')
        ]
    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )
    location = fields.Char('Location')
    webservice_key = fields.Char(
        string='Webservice key',
        help="You have to put it in 'username' of the PrestaShop "
             "Webservice api path invite"
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse used to compute the stock quantities.'
    )
    stock_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Stock Location',
        help='Location used to import stock quantities.'
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        default=lambda self: self._default_pricelist_id(),
        help="Pricelist used in sales orders",
    )
    sale_team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        help="Sales Team assigned to the imported sales orders.",
    )

    refund_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Refund Journal',
    )

    taxes_included = fields.Boolean("Use tax included prices")
    import_partners_since = fields.Datetime('Import partners since')
    import_orders_since = fields.Datetime('Import Orders since')
    import_products_since = fields.Datetime('Import Products since')
    import_refunds_since = fields.Datetime('Import Refunds since')
    import_suppliers_since = fields.Datetime('Import Suppliers since')
    language_ids = fields.One2many(
        comodel_name='prestashop.res.lang',
        inverse_name='backend_id',
        string='Languages',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'prestashop.backend'),
        string='Company',
    )
    discount_product_id = fields.Many2one(
        comodel_name='product.product',
        index=True,
        required=True,
        string='Discount Product',
    )
    shipping_product_id = fields.Many2one(
        comodel_name='product.product',
        index=True,
        required=True,
        string='Shipping Product',
    )
    importable_order_state_ids = fields.Many2many(
        comodel_name='sale.order.state',
        string='Importable sale order states',
        help="If valued only orders matching these states will be imported.",
    )

    @api.model
    def _default_pricelist_id(self):
        return self.env['product.pricelist'].search([], limit=1)

    @api.multi
    def get_environment(self, model_name,):
        self.ensure_one()
        return ConnectorEnvironment(self, model_name)

    @api.multi
    def synchronize_metadata(self):
        for backend in self:
            for model_name in [
                'prestashop.shop.group',
                'prestashop.shop'
            ]:
                # import directly, do not delay because this
                # is a fast operation, a direct return is fine
                # and it is simpler to import them sequentially
                self.env[model_name].import_batch(backend=backend)
        return True

    @api.multi
    def synchronize_basedata(self):
        for backend in self:
            for model_name in [
                'prestashop.res.lang',
                'prestashop.res.country',
                'prestashop.res.currency',
                'prestashop.account.tax',
            ]:
                env = backend.get_environment(model_name)
                importer = env.get_connector_unit(AutoMatchingImporter)
                importer.run()
            self.env['prestashop.account.tax.group'].import_batch(
                backend=backend)
            self.env['prestashop.sale.order.state'].import_batch(
                backend=backend)
        return True

    @api.multi
    def _check_connection(self):
        self.ensure_one()
        env = self.get_environment(self._name)
        adapter = env.get_connector_unit(GenericAdapter)
        with api_handle_errors('Connection failed'):
            adapter.head()

    @api.multi
    def button_check_connection(self):
        self._check_connection()
        raise exceptions.UserError(_('Connection successful'))

    @api.multi
    def import_customers_since(self):
        for backend_record in self:
            connector_env = backend_record.get_environment('res.partner')
            since_date = backend_record.import_partners_since
            connector_env.env['res.partner'].with_delay(
                priority=10
            ).import_customers_since(
                backend_record=backend_record, since_date=since_date)
        return True

    @api.multi
    def import_products(self):
        for backend_record in self:
            since_date = backend_record.import_products_since
            backend_record.env['prestashop.product.template'].with_delay(
                priority=10).import_products(backend_record, since_date)
        return True

    @api.multi
    def import_carriers(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            import_carriers.delay(session, backend_record.id, priority=10)
        return True

    @api.multi
    def update_product_stock_qty(self):
        for backend_record in self:
            backend_record.env['prestashop.product.template']\
                .with_delay().export_product_quantities(backend=backend_record)
            backend_record.env['prestashop.product.product']\
                .with_delay().export_product_quantities(backend=backend_record)
        return True

    @api.multi
    def import_stock_qty(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            import_inventory.delay(session, backend_record.id)

    @api.multi
    def import_sale_orders(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = backend_record.import_orders_since
            import_orders_since.delay(
                session,
                backend_record.id,
                since_date,
                priority=5,
            )
        return True

    @api.multi
    def import_payment_modes(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            import_batch.delay(session, 'account.payment.mode',
                               backend_record.id)
        return True

    @api.multi
    def import_refunds(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = backend_record.import_refunds_since
            import_refunds.delay(session, backend_record.id, since_date)
        return True

    @api.multi
    def import_suppliers(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = backend_record.import_suppliers_since
            import_suppliers.delay(session, backend_record.id, since_date)
        return True

    def get_version_ps_key(self, key):
        self.ensure_one()
        env = self.get_environment('_prestashop.version.key')
        keys = env.get_connector_unit(VersionKey)
        return keys.get_key(key)

    @api.model
    def _scheduler_update_product_stock_qty(self, domain=None):
        self.search(domain or []).update_product_stock_qty()

    @api.model
    def _scheduler_import_sale_orders(self, domain=None):
        self.search(domain or []).import_sale_orders()

    @api.model
    def _scheduler_import_customers(self, domain=None):
        self.search(domain or []).import_customers_since()

    @api.model
    def _scheduler_import_products(self, domain=None):
        self.search(domain or []).import_products()

    @api.model
    def _scheduler_import_carriers(self, domain=None):
        self.search(domain or []).import_carriers()

    @api.model
    def _scheduler_import_payment_methods(self, domain=None):
        backends = self.search(domain or [])
        backends.import_payment_methods()
        backends.import_refunds()

    @api.model
    def _scheduler_import_suppliers(self, domain=None):
        self.search(domain or []).import_suppliers()

    @api.multi
    def import_record(self, model_name, ext_id):
        self.ensure_one()
        session = ConnectorSession.from_env(self.env)
        import_record(session, model_name, self.id, ext_id)
        return True

    @api.multi
    def _get_locations_for_stock_quantities(self):
        root_location = (self.stock_location_id or
                         self.warehouse_id.lot_stock_id)
        locations = self.env['stock.location'].search([
            ('id', 'child_of', root_location.id),
            ('prestashop_synchronized', '=', True),
            ('usage', '=', 'internal'),
        ])
        # if we choosed a location but none where flagged
        # 'prestashop_synchronized', consider we want all of them in the tree
        if not locations:
            locations = self.env['stock.location'].search([
                ('id', 'child_of', root_location.id),
                ('usage', '=', 'internal'),
            ])
        if not locations:
            # we must not pass an empty location or we would have the
            # stock for every warehouse, which is the last thing we
            # expect
            raise exceptions.UserError(
                _('No internal location found to compute the product '
                  'quantity.')
            )
        return locations


class PrestashopShopGroup(models.Model):
    _name = 'prestashop.shop.group'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Shop Group'

    name = fields.Char('Name', required=True)
    shop_ids = fields.One2many(
        comodel_name='prestashop.shop',
        inverse_name='shop_group_id',
        readonly=True,
        string="Shops",
    )
    company_id = fields.Many2one(
        related='backend_id.company_id',
        comodel_name="res.company",
        string='Company'
    )


@prestashop
class NoModelAdapter(GenericAdapter):
    """ Used to test the connection """
    _model_name = 'prestashop.backend'
    _prestashop_model = ''


@prestashop
class ShopGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.shop.group'
    _prestashop_model = 'shop_groups'
