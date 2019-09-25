# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.component.core import Component


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.specific.price',
        inverse_name='odoo_id',
        string="PrestaShop Bindings",
    )


class PrestashopSpecificPrice(models.Model):
    _name = 'prestashop.specific.price'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.pricelist.item': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        required=True,
        ondelete='cascade',
        string='Pricelist Item',
    )
    shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='Shop',
        required=True,
    )


class SpecificPriceBinder(Component):
    _name = 'prestashop.specific.price.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.specific.price'


class SpecificPriceAdapter(Component):
    _name = 'prestashop.specific.price.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.specific.price'
    _prestashop_model = 'specific_prices'
    _export_node_name = 'specific_price'
    _export_node_name_res = 'specific_price'


class PricelistItemListener(Component):
    _name = 'product.pricelist.item.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'product.pricelist.item'

    def on_record_create(self, record, fields=None):
        binding_obj = self.env['prestashop.specific.price']
        if record.applied_on == '1_product':
            for template_binding in \
                    record.product_tmpl_id.prestashop_bind_ids:
                binding_obj.create({
                    'backend_id': template_binding.backend_id.id,
                    'odoo_id': record.id,
                    'shop_id': template_binding.default_shop_id.id,
                })
        elif record.applied_on == '0_product_variant':
            for combination_binding in \
                    record.product_id.prestashop_combinations_bind_ids:
                binding_obj.create({
                    'backend_id': combination_binding.backend_id.id,
                    'odoo_id': record.id,
                    'shop_id': combination_binding.default_shop_id.id,
                })
        for binding in record.prestashop_bind_ids:
            binding.with_delay().export_record(fields=fields)
