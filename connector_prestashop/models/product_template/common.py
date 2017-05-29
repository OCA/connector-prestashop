# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from odoo.addons.queue_job.job import job
from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop
from exporter import ProductInventoryExporter

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
        digits=dp.get_precision('Product Price'),
    )

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

    @job(default_channel='root.prestashop')
    def import_products(self, backend, since_date=None, **kwargs):
        filters = None
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
        now_fmt = fields.Datetime.now()
        self.env['prestashop.product.category'].with_delay(
            priority=15
        ).import_batch(backend=backend, filters=filters, **kwargs)
        self.env['prestashop.product.template'].with_delay(
            priority=15
        ).import_batch(backend, filters, **kwargs)
        backend.import_products_since = now_fmt
        return True

    @job(default_channel='root.prestashop')
    def export_inventory(self, backend, fields=None, **kwargs):
        """ Export the inventory configuration and quantity of a product. """
        env = backend.get_environment(self._name)
        inventory_exporter = env.get_connector_unit(ProductInventoryExporter)
        return inventory_exporter.run(self.id, fields, **kwargs)

    @api.model
    @job(default_channel='root.prestashop')
    def export_product_quantities(self, backend):
        self.search([
            ('backend_id', 'in', self.env.backend.ids),
        ]).recompute_prestashop_qty()


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
