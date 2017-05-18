# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import _, exceptions, api, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop

import logging

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceDict
except:
    _logger.debug('Cannot import from `prestapyt`')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.template',
        inverse_name='odoo_id',
        copy=False,
        string='PrestaShop Bindings',
    )
    prestashop_default_category_id = fields.Many2one(
        comodel_name='product.category',
        string='PrestaShop Default Category',
        ondelete='restrict'
    )

    @api.multi
    def update_prestashop_quantities(self):
        for template in self:
            # Recompute product template PrestaShop qty
            template.mapped('prestashop_bind_ids').recompute_prestashop_qty()
            # Recompute variant PrestaShop qty
            template.mapped(
                'product_variant_ids.prestashop_bind_ids'
            ).recompute_prestashop_qty()
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
    wholesale_price = fields.Float(
        string='Cost Price',
        digits_compute=dp.get_precision('Product Price'),
    )

    @api.multi
    def recompute_prestashop_qty(self):
        for product_binding in self:
            new_qty = product_binding._prestashop_qty()
            if product_binding.quantity != new_qty:
                product_binding.quantity = new_qty
        return True

    def _prestashop_qty(self):
        root_location = (self.backend_id.stock_location_id or
                         self.backend_id.warehouse_id.lot_stock_id)
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
        return self.with_context(location=locations.ids).qty_available


@prestashop
class ProductInventoryAdapter(GenericAdapter):
    _model_name = '_import_stock_available'
    _prestashop_model = 'stock_availables'
    _export_node_name = 'stock_available'

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
            client.edit(self._prestashop_model, {
                self._export_node_name: stock
            })


@prestashop
class PrestashopProductTags(GenericAdapter):
    _model_name = '_prestashop_product_tag'
    _prestashop_model = 'tags'
    _export_node_name = 'tag'

    def search(self, filters=None):
        res = self.client.get(self._prestashop_model, options=filters)
        tags = res[self._prestashop_model]
        if not tags:
            return []
        tags = tags[self._export_node_name]
        if isinstance(tags, dict):
            return [tags]
        return tags
