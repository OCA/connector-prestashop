# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.addons.component.core import Component
from odoo.exceptions import ValidationError


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.specific.price',
        inverse_name='odoo_id',
        string="PrestaShop Bindings",
    )

    @api.constrains('prestashop_bind_ids', 'applied_on', 'compute_price')
    def _check_supported_by_prestashop_catalog_manager(self):
        for item in self:
            if not item.prestashop_bind_ids:
                continue
            if item.applied_on not in ('1_product', '0_product_variant'):
                raise ValidationError(_(
                    'Error! Currently only Apply on Product or Product '
                    'variant is supported by PrestaShop catalog manager!'))
            if item.compute_price not in ('fixed', 'percentage'):
                raise ValidationError(_(
                    'Error! Currently only Compute price based on Fixed price '
                    'or Percentage discount is supported by PrestaShop '
                    'catalog manager!'))
        return True


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

    def _check_bindings(self, record):
        binding_obj = self.env['prestashop.specific.price']
        if record.applied_on not in ('1_product', '0_product_variant'):
            return
        if record.applied_on == '1_product':
            product_tmpl = record.product_tmpl_id
        else:
            product_tmpl = record.product_id.product_tmpl_id
        for template_binding in product_tmpl.prestashop_bind_ids:
            backend = template_binding.backend_id
            if record.pricelist_id != backend.pricelist_id:
                continue
            record_binding = binding_obj.search([
                ('backend_id', '=', backend.id),
                ('odoo_id', '=', record.id),
            ])
            if record_binding:
                continue
            binding_obj.create({
                'backend_id': backend.id,
                'odoo_id': record.id,
                'shop_id': template_binding.default_shop_id.id,
            })

    def on_record_create(self, record, fields=None):
        self._check_bindings(record)
        for binding in record.prestashop_bind_ids:
            binding.with_delay().export_record(fields=fields)

    def on_record_write(self, record, fields=None):
        if fields:
            self._check_bindings(record)
        for binding in record.prestashop_bind_ids:
            binding.with_delay().export_record(fields=fields)

    def on_record_unlink(self, record, fields=None):
        for binding in record.prestashop_bind_ids:
            if not binding.prestashop_id:
                continue
            binding.with_delay().export_delete_record(
                binding._name, binding.backend_id, binding.prestashop_id,
                record)
