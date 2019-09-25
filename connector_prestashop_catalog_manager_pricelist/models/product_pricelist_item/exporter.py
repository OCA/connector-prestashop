# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    changed_by, m2o_to_external, mapping) 


class SpecificPriceMapper(Component):
    _name = 'prestashop.specific.price.export.mapper'
    _inherit = 'prestashop.export.mapper'
    _apply_on = 'prestashop.specific.price'

    direct = [
        (m2o_to_external('shop_id'), 'id_shop'),
        ('min_quantity', 'from_quantity'),
        ('date_start', 'from'),
        ('date_end', 'to',),
    ]

    @mapping
    def defaults(self, record):
        return {
            'id_cart': 0,
            'id_currency': 0,
            'id_country': 0,
            'id_group': 0,
            'id_customer': 0,
        }

    @changed_by('applied_on', 'product_tmpl_id', 'product_id')
    @mapping
    def product_or_combination(self, record):
        vals = {
            'id_product': 0,
            'id_product_attribute': 0,
        }
        template_binder = self.binder_for('prestashop.product.template')
        combination_binder = self.binder_for('prestashop.product.combination')
        if record.applied_on == '1_product':
            vals['id_product'] = template_binder.to_external(
                record.product_tmpl_id, wrap=True)
        elif record.applied_on == '0_product_variant':
            vals['id_product'] = combination_binder.to_external(
                record.product_id.product_tmpl_id, wrap=True)
            vals['id_product_attribute'] = combination_binder.to_external(
                record.product_id, wrap=True)
        return vals

    @changed_by('compute_price', 'fixed_price', 'percent_price')
    @mapping
    def price_and_reduction(self, record):
        vals = {
            'price': -1,
            'reduction': 0,
            'reduction_type': 'amount',
            'reduction_tax': 0,
        }
        if record.compute_price == 'fixed':
            vals['price'] = record.fixed_price
        elif record.compute_price == 'percentage':
            vals['reduction'] = record.percent_price / 100
            vals['reduction_type'] = 'percentage'
        return vals


class SpecificPriceExporter(Component):
    _name = 'prestashop.specific.price.exporter'
    _inherit = 'prestashop.exporter'
    _apply_on = 'prestashop.specific.price'
