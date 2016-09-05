# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pytz
from datetime import datetime

from openerp import models, fields, api


from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.connector.session import ConnectorSession
from ..unit.import_synchronizer import (
    import_batch,
    import_customers_since,
    import_orders_since,
    import_products,
    import_refunds,
    import_carriers,
    import_suppliers,
    import_record,
    export_product_quantities,
)
from ..unit.direct_binder import DirectBinder
from ..connector import get_environment

from openerp.addons.connector_prestashop.product import import_inventory

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
            ('1.6.0.11', '>= 1.6.0.11'),
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

    def get_version_ps_key(self, key):
        keys_conversion = {
            '1.6.0.9': {
                'product_option_value': 'product_option_values',
                'category': 'categories',
                'order_slip_detail': 'order_slip_details',
                'group': 'groups',
                'order_row': 'order_rows',
                'tax': 'taxes',
                'image': 'images',
            },
            # singular names as < 1.6.0.9
            '1.6.0.11': {},
        }
        if self.version == '1.6.0.9':
            key = keys_conversion[self.version][key]
        return key

    def _scheduler_launch(self, cr, uid, callback, domain=None,
                          context=None):
        if domain is None:
            domain = []
        ids = self.search(cr, uid, domain, context=context)
        if ids:
            callback(cr, uid, ids, context=context)

    def _scheduler_update_product_stock_qty(self, cr, uid, domain=None,
                                            context=None):
        self._scheduler_launch(cr, uid, self.update_product_stock_qty,
                               domain=domain, context=context)

    def _scheduler_import_sale_orders(self, cr, uid, domain=None,
                                      context=None):
        self._scheduler_launch(cr, uid, self.import_sale_orders, domain=domain,
                               context=context)

    def _scheduler_import_customers(self, cr, uid, domain=None,
                                    context=None):
        self._scheduler_launch(cr, uid, self.import_customers_since,
                               domain=domain, context=context)

    def _scheduler_import_products(self, cr, uid, domain=None, context=None):
        self._scheduler_launch(cr, uid, self.import_products, domain=domain,
                               context=context)

    def _scheduler_import_carriers(self, cr, uid, domain=None, context=None):
        self._scheduler_launch(cr, uid, self.import_carriers, domain=domain,
                               context=context)

    def _scheduler_import_payment_methods(self, cr, uid, domain=None,
                                          context=None):
        self._scheduler_launch(cr, uid, self.import_payment_methods,
                               domain=domain, context=context)

        self._scheduler_launch(cr, uid, self.import_refunds,
                               domain=domain, context=context)

    def _scheduler_import_suppliers(self, cr, uid, domain=None, context=None):
        self._scheduler_launch(cr, uid, self.import_suppliers,
                               domain=domain, context=context)

    def import_record(self, cr, uid, backend_id, model_name, ext_id,
                      context=None):
        session = ConnectorSession(cr, uid, context=context)
        import_record(session, model_name, backend_id, ext_id)
        return True


class PrestashopBinding(models.AbstractModel):
    _name = 'prestashop.binding'
    _inherit = 'external.binding'
    _description = 'PrestaShop Binding (abstract)'

    # 'openerp_id': openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        required=True,
        ondelete='restrict'
    )
    # TODO : do I keep the char like in Magento, or do I put a PrestaShop ?
    prestashop_id = fields.Integer('ID on PrestaShop')

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'An record with same ID already exists on PrestaShop.'),
    ]

    @api.multi
    def resync(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        func = import_record
        if self.env.context and self.env.context.get('connector_delay'):
            func = import_record.delay
        for record in self:
            func(session, self._name, record.backend_id.id,
                 record.prestashop_id)
        return True


# TODO remove external.shop.group from connector_ecommerce
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


# TODO migrate from sale.shop
class PrestashopShop(models.Model):
    _name = 'prestashop.shop'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Shop'

    @api.multi
    @api.depends('shop_group_id', 'shop_group_id.backend_id')
    def _compute_backend_id(self):
        self.backend_id = self.shop_group_id.backend_id.id

    name = fields.Char(
        string='Name',
        help="The name of the method on the backend",
        required=True
    )
    shop_group_id = fields.Many2one(
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
        required=True,
        ondelete='cascade',
    )
    openerp_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='WareHouse',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        compute='_compute_backend_id',
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        store=True,
    )
    default_url = fields.Char('Default url')


class StockLocation(models.Model):
    _inherit = 'stock.warehouse'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.shop',
        inverse_name='openerp_id',
        readonly=True,
        string='PrestaShop Bindings',
    )


class PrestashopResLang(models.Model):
    _name = 'prestashop.res.lang'
    _inherit = 'prestashop.binding'
    _inherits = {'res.lang': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='res.lang',
        required=True,
        ondelete='cascade',
        string='Language',
    )
    active = fields.Boolean(
        string='Active in prestashop',
        default=False,
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]


class ResLang(models.Model):
    _inherit = 'res.lang'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.lang',
        inverse_name='openerp_id',
        readonly=True,
        string='PrestaShop Bindings',
    )


class PrestashopResCountry(models.Model):
    _name = 'prestashop.res.country'
    _inherit = 'prestashop.binding'
    _inherits = {'res.country': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='res.country',
        required=True,
        ondelete='cascade',
        string='Country',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]


class ResCountry(models.Model):
    _inherit = 'res.country'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.country',
        inverse_name='openerp_id',
        readonly=True,
        string='prestashop Bindings',
    )


class PrestashopResCurrency(models.Model):
    _name = 'prestashop.res.currency'
    _inherit = 'prestashop.binding'
    _inherits = {'res.currency': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.currency',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
        readonly=True
    )


class PrestashopAccountTax(models.Model):
    _name = 'prestashop.account.tax'
    _inherit = 'prestashop.binding'
    _inherits = {'account.tax': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax',
        required=True,
        ondelete='cascade'
    )


class AccountTax(models.Model):
    _inherit = 'account.tax'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.account.tax',
        inverse_name='openerp_id',
        string='prestashop Bindings',
        readonly=True,
    )


class PrestashopAccountTaxGroup(models.Model):
    _name = 'prestashop.account.tax.group'
    _inherit = 'prestashop.binding'
    _inherits = {'account.tax.group': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='account.tax.group',
        string='Tax Group',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.account.tax.group',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
        readonly=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        required=True,
        string='Company',
    )
