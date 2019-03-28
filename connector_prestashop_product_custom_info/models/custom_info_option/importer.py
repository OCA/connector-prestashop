# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ProductFeatureValueMapper(Component):
    _name = 'prestashop.product.feature.value.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.feature.value'

    direct = [
        ('value', 'name'),
    ]

    @mapping
    def property_ids(self, record):
        binder = self.binder_for('prestashop.product.feature')
        property = binder.to_internal(record['id_feature'], unwrap=True)
        return {'property_ids': [(6, 0, [property.id])]}

    @mapping
    def custom(self, record):
        return {'custom': bool(int(record['custom']))}


class ProductFeatureValueImporter(Component):
    _name = 'prestashop.product.feature.value.importer'
    _inherit = 'prestashop.translatable.record.importer'
    _apply_on = 'prestashop.product.feature.value'

    _translatable_fields = {
        'prestashop.product.feature.value': [
            'value',
        ],
    }

    def _has_to_skip(self):
        feature_binder = self.binder_for('prestashop.product.feature')
        property = feature_binder.to_internal(
            self.prestashop_record['id_feature'], unwrap=True)
        # do not import PS feature value if Odoo info property does not have
        # the "PrestaShop" info category
        return bool(property and property.category_id != 
                    self.backend_record.product_custom_info_category_id)

    def _import_dependencies(self):
        self._import_dependency(
            self.prestashop_record['id_feature'], 'prestashop.product.feature')


class ProductFeatureValueBatchImporter(Component):
    _name = 'prestashop.product.feature.value.delayed.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = 'prestashop.product.feature.value'
