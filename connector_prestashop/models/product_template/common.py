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
        inverse_name='odoo_id',
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
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.template': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        ondelete='cascade',
        string='Template',
        oldname='openerp_id',
    )
    # TODO FIXME what name give to field present in
    # prestashop_product_product and product_product
    always_available = fields.Boolean(
        string='Active',
        default=True,
        help='If checked, this product is considered always available')
    quantity = fields.Float(
        string='Computed Quantity',
        help="Last computed quantity to send to PrestaShop."
    )
    description_html = fields.Html(
        string='Description',
        translate=True,
        help="HTML description from PrestaShop",
    )
    description_short_html = fields.Html(
        string='Short Description',
        translate=True,
    )
    date_add = fields.Datetime(
        string='Created at (in PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated at (in PrestaShop)',
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
        string='Available for Order Taking',
        default=True,
    )
    show_price = fields.Boolean(string='Display Price', default=True)
    combinations_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='main_template_id',
        string='Combinations'
    )
    reference = fields.Char(string='Original reference')
    on_sale = fields.Boolean(string='Show on sale icon')

    @api.multi
    def recompute_prestashop_qty(self):
        for product_binding in self:
            new_qty = product_binding._prestashop_qty()
            if product_binding.quantity != new_qty:
                product_binding.quantity = new_qty
        return True

    def _prestashop_qty(self):
        locations = self.env['stock.location'].search([
            ('id', 'child_of', self.backend_id.warehouse_id.lot_stock_id.id),
            ('prestashop_synchronized', '=', True),
            ('usage', '=', 'internal'),
        ])
        return self.with_context(location=locations.ids).qty_available


@prestashop
class TemplateAdapter(GenericAdapter):
    _model_name = 'prestashop.product.template'
    _prestashop_model = 'products'
    _export_node_name = 'product'


    @api.multi
    def update_prestashop_qty(self):
        for product in self:
            if product.product_variant_count > 1:
                # Recompute qty in combination binding
                for combination_binding in product.prestashop_bind_ids:
                    combination_binding.recompute_prestashop_qty()
            # Recompute qty in product template binding if any combination
            # if modified
            for prestashop_product in \
                    product.product_tmpl_id.prestashop_bind_ids:
                prestashop_product.recompute_prestashop_qty()

    @api.multi
    def update_prestashop_quantities(self):
        for product in self:
            product_template = product.product_tmpl_id
            prestashop_combinations = (
                len(product_template.product_variant_ids) > 1 and
                product_template.product_variant_ids) or []
            if not prestashop_combinations:
                for prestashop_product in product_template.prestashop_bind_ids:
                    prestashop_product.recompute_prestashop_qty()
            else:
                for prestashop_combination in prestashop_combinations:
                    for combination_binding in \
                            prestashop_combination.prestashop_bind_ids:
                        combination_binding.recompute_prestashop_qty()
        return True

    def get(self, options=None):
        return self.client.get(self._prestashop_model, options=options)

    def export_quantity(self, filters, quantity):
        self.export_quantity_url(
            filters,
            quantity,
        )

        shops = self.env['prestashop.shop'].search([
            ('backend_id', '=', self.backend_record.id),
            ('default_url', '!=', False),
        ])
        for shop in shops:
            url = '%s/api' % shop.default_url
            key = self.backend_record.webservice_key
            client = PrestaShopWebServiceDict(url, key)
            self.export_quantity_url(filters, quantity, client=client)

    def export_quantity_url(self, filters, quantity, client=None):
        if client is None:
            client = self.client
        response = client.search(self._prestashop_model, filters)
        for stock_id in response:
            res = client.get(self._prestashop_model, stock_id)
            first_key = res.keys()[0]
            stock = res[first_key]
            stock['quantity'] = int(quantity)
            try:
                client.edit(self._prestashop_model, stock['id'], {
                    self._export_node_name: stock
                })
            # TODO: investigate the silent errors
            except PrestaShopWebServiceError:
                pass
            except ElementTree.ParseError:
                pass
