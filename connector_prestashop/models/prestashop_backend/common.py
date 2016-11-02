# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
import pytz

from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.session import ConnectorSession
from ...unit.direct_binder import DirectBinder
from ...unit.importer import import_batch, import_record
from ...connector import get_environment
from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop

from ..product_template.exporter import export_product_quantities
from ..product_template.importer import import_inventory
from ..res_partner.importer import import_customers_since
from ..delivery_carrier.importer import import_carriers
from ..product_supplierinfo.importer import import_suppliers
from ..account_invoice.importer import import_refunds
from ..product_template.importer import import_products
from ..sale_order.importer import import_orders_since

from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


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
            ('1.6.0.11', '>= 1.6.0.11'),
            ('1.6.1.2', '>= 1.6.1.2'),
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

    @api.multi
    def synchronize_metadata(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            for model in [
                'prestashop.shop.group',
                'prestashop.shop'
            ]:
                # import directly, do not delay because this
                # is a fast operation, a direct return is fine
                # and it is simpler to import them sequentially
                import_batch(session, model, backend.id)
        return True

    @api.multi
    def synchronize_basedata(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            for model_name in [
                'prestashop.res.lang',
                'prestashop.res.country',
                'prestashop.res.currency',
                'prestashop.account.tax',
            ]:
                env = get_environment(session, model_name, backend.id)
                directBinder = env.get_connector_unit(DirectBinder)
                directBinder.run()

            import_batch(session, 'prestashop.account.tax.group', backend.id)
            import_batch(session, 'prestashop.sale.order.state', backend.id)
        return True

    def _date_as_user_tz(self, dtstr):
        if not dtstr:
            return None
        timezone = pytz.timezone(self.env.user.partner_id.tz or 'utc')
        dt = datetime.strptime(dtstr, DEFAULT_SERVER_DATETIME_FORMAT)
        dt = pytz.utc.localize(dt)
        dt = dt.astimezone(timezone)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def import_customers_since(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            since_date = self._date_as_user_tz(
                backend_record.import_partners_since)
            import_customers_since.delay(
                session,
                backend_record.id,
                since_date,
                priority=10,
            )
        return True

    @api.multi
    def import_products(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            since_date = self._date_as_user_tz(
                backend_record.import_products_since)
            import_products.delay(
                session,
                backend_record.id,
                since_date,
                priority=10)
        return True

    @api.multi
    def import_carriers(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            import_carriers.delay(session, backend_record.id, priority=10)
        return True

    @api.multi
    def update_product_stock_qty(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            export_product_quantities.delay(session, backend_record.id)
        return True

    @api.multi
    def import_stock_qty(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            import_inventory.delay(session, backend_record.id)

    @api.multi
    def import_sale_orders(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            since_date = self._date_as_user_tz(
                backend_record.import_orders_since)
            import_orders_since.delay(
                session,
                backend_record.id,
                since_date,
                priority=5,
            )
        return True

    @api.multi
    def import_payment_methods(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            import_batch.delay(session, 'payment.method', backend_record.id)
        return True

    @api.multi
    def import_refunds(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            since_date = self._date_as_user_tz(
                backend_record.import_refunds_since)
            import_refunds.delay(session, backend_record.id, since_date)
        return True

    @api.multi
    def import_suppliers(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            since_date = self._date_as_user_tz(
                backend_record.import_suppliers_since)
            import_suppliers.delay(session, backend_record.id, since_date)
        return True

    keys_conversion = {
        '1.6.0.9': {
            'product_option_value': 'product_option_values',
            'category': 'categories',
            'order_slip': 'order_slips',
            'order_slip_detail': 'order_slip_details',
            'group': 'groups',
            'order_row': 'order_rows',
            'tax': 'taxes',
            'image': 'images',
            'combinations': 'combinations',
            'tag': 'tags',
        },
        # singular names as < 1.6.0.9
        '1.6.0.11': {},
        '1.6.1.2': {
            'product_option_value': 'product_option_value',
            'category': 'category',
            'image': 'image',
            'order_slip': 'order_slip',
            'order_slip_detail': 'order_slip_detail',
            'group': 'group',
            'order_row': 'order_row',
            'tax': 'taxes',
            'combinations': 'combination',
            'product_features': 'product_feature',
            'tag': 'tag',
            'messages': 'customer_messages',
        },
    }

    @api.multi
    def get_environment(self, model_name, session=None):
        self.ensure_one()
        if not session:
            session = ConnectorSession.from_env(self.env)
        return ConnectorEnvironment(self, session, model_name)

    def get_version_ps_key(self, key):
        if self.version in ['1.6.0.9', '1.6.1.2']:
            return self.keys_conversion[self.version][key]
        return key

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
        session = ConnectorSession()
        import_record(session, model_name, self.id, ext_id)
        return True

    @api.multi
    def get_stock_locations(self):
        self.ensure_one()
        locations = self.env['stock.location'].search([
            ('id', 'child_of', self.stock_location_id.id or
                self.warehouse_id.lot_stock_id.id),
            ('prestashop_synchronized', '=', True),
            ('usage', '=', 'internal'),
        ])
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
class ShopGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.shop.group'
    _prestashop_model = 'shop_groups'
