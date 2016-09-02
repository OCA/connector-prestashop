# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models

try:
    from xml.etree import cElementTree as ElementTree
except ImportError, e:
    from xml.etree import ElementTree

from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError

from ...unit.backend_adapter import GenericAdapter

from ...backend import prestashop


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.template',
        inverse_name='openerp_id',
        copy=False,
        string='PrestaShop Bindings',
    )

    @api.multi
    def update_prestashop_quantities(self):
        for template in self:
            for prestashop_template in template.prestashop_bind_ids:
                prestashop_template.recompute_prestashop_qty()
            ps_combinations = template.product_variant_ids
            for ps_combinations in ps_combinations.prestashop_bind_ids:
                ps_combinations.recompute_prestashop_qty()
        return True


class PrestashopProductTemplate(models.Model):
    _name = 'prestashop.product.template'
    _inherit = 'prestashop.binding'
    _inherits = {'product.template': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        ondelete='cascade',
        string='Template',
    )
    # TODO FIXME what name give to field present in
    # prestashop_product_product and product_product
    always_available = fields.Boolean(
        string='Active',
        default=True,
        help='if check, this object is always available')
    quantity = fields.Float(
        string='Computed Quantity',
        help="Last computed quantity to send on PrestaShop."
    )
    description_html = fields.Html(
        string='Description',
        translate=True,
        help="Description html from PrestaShop",
    )
    description_short_html = fields.Html(
        string='Short Description',
        translate=True,
    )
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True
    )
    default_shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='Default shop',
        required=True
    )
    link_rewrite = fields.Char(
        string='Friendly URL',
        translate=True,
    )
    available_for_order = fields.Boolean(
        string='Available For Order',
        default=True,
    )
    show_price = fields.Boolean(string='Show Price', default=True)
    combinations_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='main_template_id',
        string='Combinations'
    )
    reference = fields.Char(string='Original reference')
    on_sale = fields.Boolean(string='Show on sale icon')

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
    ]

    @api.multi
    def recompute_prestashop_qty(self):
        for product in self:
            new_qty = product._prestashop_qty()
            product.write({
                'quantity': new_qty,
            })
        return True

    def _prestashop_qty(self):
        location_id = self.backend_id.warehouse_id.lot_stock_id.id
        return self.with_context(location=location_id).qty_available


@prestashop
class TemplateAdapter(GenericAdapter):
    _model_name = 'prestashop.product.template'
    _prestashop_model = 'products'
    _export_node_name = 'product'


@prestashop
class ProductInventoryAdapter(GenericAdapter):
    _model_name = '_import_stock_available'
    _prestashop_model = 'stock_availables'
    _export_node_name = 'stock_available'

    def get(self, options=None):
        api = self.connect()
        return api.get(self._prestashop_model, options=options)

    def export_quantity(self, filters, quantity):
        self.export_quantity_url(
            self.backend_record.location,
            self.backend_record.webservice_key,
            filters,
            quantity
        )

        shops = self.env['prestashop.shop'].search([
            ('backend_id', '=', self.backend_record.id),
            ('default_url', '!=', False),
        ])
        for shop in shops:
            self.export_quantity_url(
                '%s/api' % shop.default_url,
                self.backend_record.webservice_key,
                filters,
                quantity
            )

    def export_quantity_url(self, url, key, filters, quantity):
        api = PrestaShopWebServiceDict(url, key)
        response = api.search(self._prestashop_model, filters)
        for stock_id in response:
            res = api.get(self._prestashop_model, stock_id)
            first_key = res.keys()[0]
            stock = res[first_key]
            stock['quantity'] = int(quantity)
            try:
                api.edit(self._prestashop_model, stock['id'], {
                    self._export_node_name: stock
                })
            # TODO: investigate the silent errors
            except PrestaShopWebServiceError:
                pass
            except ElementTree.ParseError:
                pass
