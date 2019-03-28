# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ProductFeatureMapper(Component):
    _name = 'prestashop.product.feature.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.feature'

    direct = [
        ('name', 'name'),
        ('position', 'sequence'),
    ]

    @mapping
    def template_id(self, record):
        return {'template_id':
                self.backend_record.product_custom_info_template_id.id}

    @only_create
    @mapping
    def category_id(self, record):
        return {'category_id':
                self.backend_record.product_custom_info_category_id.id}

    @mapping
    def field_type(self, record):
        return {'field_type': 'id'}


class ProductFeatureImporter(Component):
    _name = 'prestashop.product.feature.importer'
    _inherit = 'prestashop.translatable.record.importer'
    _apply_on = 'prestashop.product.feature'

    _translatable_fields = {
        'prestashop.product.feature': [
            'name',
        ],
    }

    def _has_to_skip(self):
        property = self.binder.to_internal(
            self.prestashop_record['id'], unwrap=True)
        # do not import PS feature if Odoo info property does not have the
        # "PrestaShop" info category
        return bool(property and property.category_id !=
                    self.backend_record.product_custom_info_category_id)


class ProductFeatureBatchImporter(Component):
    _name = 'prestashop.product.feature.delayed.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = 'prestashop.product.feature'
