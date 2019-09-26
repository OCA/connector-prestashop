# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    changed_by, m2o_to_external, mapping)


def to_empty_date(field):
    """ A modifier intended to be used on the ``direct`` mappings.

    Replace Odoo empty date by PrestaShop '0000-00-00 00:00:00' date.

    Example::

        direct = [(to_empty_date('source'), 'target')]

    :param field: name of the source field in the record
    """
    def modifier(self, record, to_attr):
        if callable(field):
            result = field(self, record, to_attr)
        else:
            result = record[field]
        if not result:
            return '0000-00-00 00:00:00'
        return result
    return modifier


class SpecificPriceMapper(Component):
    _name = 'prestashop.specific.price.export.mapper'
    _inherit = 'prestashop.export.mapper'
    _apply_on = 'prestashop.specific.price'

    direct = [
        (m2o_to_external('shop_id'), 'id_shop'),
        (to_empty_date('date_start'), 'from'),
        (to_empty_date('date_end'), 'to',),
    ]

    @mapping
    def requireds(self, record):
        return {
            'id_cart': 0,
            'id_currency': 0,
            'id_country': 0,
            'id_group': 0,
            'id_customer': 0,
        }

    @changed_by('min_quantity')
    @mapping
    def from_quantity(self, record):
        return {'from_quantity': max(1, record.min_quantity)}

    @changed_by('applied_on', 'product_tmpl_id', 'product_id')
    @mapping
    def product_or_combination(self, record):
        vals = {
            'id_product': 0,
            'id_product_attribute': 0,
        }
        if record.applied_on not in ('1_product', '0_product_variant'):
            return vals
        template_binder = self.binder_for('prestashop.product.template')
        combination_binder = self.binder_for('prestashop.product.combination')
        if record.applied_on == '1_product':
            product_tmpl = record.product_tmpl_id
        else:
            product_tmpl = record.product_id.product_tmpl_id
            vals['id_product_attribute'] = combination_binder.to_external(
                record.product_id, wrap=True)
        vals['id_product'] = template_binder.to_external(
            product_tmpl, wrap=True)
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
        if record.compute_price not in ('fixed', 'percentage'):
            return vals
        if record.compute_price == 'fixed':
            vals['price'] = record.fixed_price
        else:
            vals['reduction'] = record.percent_price / 100
            vals['reduction_type'] = 'percentage'
        return vals


class SpecificPriceExporter(Component):
    _name = 'prestashop.specific.price.exporter'
    _inherit = 'prestashop.exporter'
    _apply_on = 'prestashop.specific.price'
