# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

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
                'product_variant_ids.prestashop_combination_bind_ids'
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
    out_of_stock = fields.Selection([
        ('0', 'Refuse order'),
        ('1', 'Accept order'),
        ('2', 'Default prestashop')],
        string='If stock shortage'
    )

    @api.multi
    def recompute_prestashop_qty(self):
        # group products by backend
        backends = defaultdict(set)
        for product in self:
            backends[product.backend_id].add(product.id)

        for backend, product_ids in backends.iteritems():
            products = self.browse(product_ids)
            products._recompute_prestashop_qty_backend(backend)
        return True

    @api.multi
    def _recompute_prestashop_qty_backend(self, backend):
        locations = backend._get_locations_for_stock_quantities()
        self_loc = self.with_context(location=locations.ids,
                                     compute_child=False)
        for product in self_loc:
            if product.type == 'product':
                new_qty = product._prestashop_qty()
                if product.quantity != new_qty:
                    product.quantity = new_qty
        return True

    @api.multi
    def _prestashop_qty(self):
        return self.qty_available

    @job(default_channel='root.prestashop')
    def import_products(self, backend, since_date=None, **kwargs):
        filters = None
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
        now_fmt = fields.Datetime.now()

        self.env['prestashop.product.category'].import_batch(
            backend, filters=filters, priority=10)

        self.env['prestashop.product.template'].import_batch(
            backend, filters=filters, priority=15)

        backend.import_products_since = now_fmt
        return True

    @job(default_channel='root.prestashop')
    def import_inventory(self, backend):
        with backend.work_on('_import_stock_available') as work:
            importer = work.component(usage='batch.importer')
            return importer.run()

    @job(default_channel='root.prestashop')
    def export_inventory(self, fields=None):
        """ Export the inventory configuration and quantity of a product. """
        backend = self.backend_id
        with backend.work_on('prestashop.product.template') as work:
            exporter = work.component(usage='inventory.exporter')
            return exporter.run(self, fields)

    @job(default_channel='root.prestashop')
    def export_product_quantities(self, backend=None):
        self.search([('backend_id', '=', backend.id)]
                    ).recompute_prestashop_qty()


class TemplateAdapter(Component):
    _name = 'prestashop.product.template.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.template'
    _prestashop_model = 'products'
    _export_node_name = 'product'


class ProductInventoryAdapter(Component):
    _name = '_import_stock_available.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = '_import_stock_available'
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
            stock['quantity'] = int(quantity['quantity'])
            stock['out_of_stock'] = int(quantity['out_of_stock'])
            client.edit(self._prestashop_model, {
                self._export_node_name: stock
            })


class PrestashopProductTagsModel(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = '_prestashop_product_tag'


class PrestashopProductTags(Component):
    _name = 'prestashop.product.tag.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = '_prestashop_product_tag'
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


class PrestashopProductQuantityListener(Component):
    _name = 'prestashop.product.quantity.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['prestashop.product.combination',
                 'prestashop.product.template']

    def _get_inventory_fields(self):
        # fields which should not trigger an export of the products
        # but an export of their inventory
        return ('quantity', 'out_of_stock')

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        inventory_fields = list(
            set(fields).intersection(self._get_inventory_fields())
        )
        if inventory_fields:
            record.with_delay(priority=20).export_inventory(
                fields=inventory_fields
            )
