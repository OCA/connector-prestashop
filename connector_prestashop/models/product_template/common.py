# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, fields, models

try:
    from xml.etree import cElementTree as ElementTree
except ImportError, e:
    from xml.etree import ElementTree

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop
from openerp.addons.connector.session import ConnectorSession
from ..product_template.exporter import export_inventory

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
except ImportError:
    _logger.debug('Can not `from prestapyt import PrestaShopWebServiceDict '
                  'or PrestaShopWebServiceError`.')


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

    @api.multi
    def force_export_stock(self):
        session = ConnectorSession.from_env(self.env)
        for template in self:
            if template.product_variant_count > 1:
                for binding in template.mapped(
                        'product_variant_ids.prestashop_bind_ids'):
                    export_inventory.delay(
                        session,
                        'prestashop.product.combination',
                        binding.id,
                        fields=['quantity'],
                        priority=20
                    )
            else:
                for binding in template.prestashop_bind_ids:
                    export_inventory.delay(
                        session,
                        'prestashop.product.template',
                        binding.id,
                        fields=['quantity'],
                        priority=20
                    )

    def _prestashop_qty(self):
        locations = self.backend_id.get_stock_locations()
        qty_available = self.with_context(location=locations.ids).qty_available
        return qty_available - self.outgoing_qty

    @api.multi
    def recompute_prestashop_qty(self):
        for product_binding in self:
            new_qty = product_binding._prestashop_qty()
            if product_binding.quantity != new_qty:
                product_binding.quantity = new_qty if new_qty >= 0.0 else 0.0
            # Recompute variants if is needed
            if product_binding.product_variant_count > 1:
                for variant in product_binding.mapped(
                        'product_variant_ids.prestashop_bind_ids'):
                    variant.recompute_prestashop_qty()
        return True


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
                client.edit(
                    self._prestashop_model, {self._export_node_name: stock})
            # TODO: investigate the silent errors
            except PrestaShopWebServiceError:
                pass
            except ElementTree.ParseError:
                pass


@prestashop
class PrestashopProductTags(GenericAdapter):
    _model_name = '_prestashop_product_tag'
    _prestashop_model = 'tags'
    _export_node_name = 'tag'

    def search(self, filters=None):
        res = self.client.get(self._prestashop_model, options=filters)
        tags = res[self._prestashop_model][self._export_node_name]
        if isinstance(tags, dict):
            return [tags]
        return tags
