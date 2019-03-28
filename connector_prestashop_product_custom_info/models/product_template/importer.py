# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ProductTemplateMapper(Component):
    _inherit = 'prestashop.product.template.mapper'

    @only_create
    @mapping
    def custom_info_template_id(self, record):
        return {'custom_info_template_id':
                self.backend_record.product_custom_info_template_id.id}


class ProductTemplateImporter(Component):
    _inherit = 'prestashop.product.template.importer'

    def _import_dependencies(self):
        super(ProductTemplateImporter, self)._import_dependencies()
        self._import_features_and_values()

    def _import_features_and_values(self):
        template = self.binder.to_internal(
            self.prestashop_record['id'], unwrap=True)
        # do not import PS features and values if Odoo product template does
        # not have the "PrestaShop" info template
        if (template and template.custom_info_template_id !=
                self.backend_record.product_custom_info_template_id):
            return

        associations = self.prestashop_record.get('associations', {})
        features = associations.get(
            'product_features', {}).get(
                'product_feature', [])
        if not isinstance(features, list):
            features = [features]
        for feature in features:
            self._import_dependency(
                feature['id'], 'prestashop.product.feature')
            self._import_dependency(
                feature['id_feature_value'],
                'prestashop.product.feature.value')

    def _after_import(self, binding):
        super(ProductTemplateImporter, self)._after_import(binding)
        self._set_custom_info_ids(binding)

    def _set_custom_info_ids(self, binding):
        # do not set PS features and values if Odoo product template does not
        # have the "PrestaShop" info template
        template = binding.odoo_id
        if (template.custom_info_template_id !=
                self.backend_record.product_custom_info_template_id):
            return

        feature_binder = self.binder_for('prestashop.product.feature')
        feature_value_binder = self.binder_for(
            'prestashop.product.feature.value')
        new_values = self.env['custom.info.value']

        associations = self.prestashop_record.get('associations', {})
        features = associations.get(
            'product_features', {}).get(
                'product_feature', [])
        if not isinstance(features, list):
            features = [features]
        for feature in features:
            # do not set PS feature and value if Odoo info property does not
            # have the "PrestaShop" info category
            property = feature_binder.to_internal(feature['id'], unwrap=True)
            if (property.category_id !=
                    self.backend_record.product_custom_info_category_id):
                continue

            option = feature_value_binder.to_internal(
                feature['id_feature_value'], unwrap=True)
            value = template.custom_info_ids.filtered(
                lambda v: v.property_id == property)
            if value:
                value.write({'value_id': option.id})
            else:
                value = self.env['custom.info.value'].create({
                    'model': 'product.template',
                    'res_id': template.id,
                    'property_id': property.id,
                    'value_id': option.id,
                    })
            new_values |= value

            # remove old Odoo info options from PS custom feature values
            old_options = property.option_ids.filtered(
                lambda o: o.prestashop_bind_ids.custom and not o.value_ids)
            old_options.unlink()

        # remove old Odoo info values with "PrestaShop" info category
        ps_values = template.custom_info_ids.filtered(
            lambda v: (v.category_id ==
                       self.backend_record.product_custom_info_category_id))
        old_values = ps_values - new_values
        old_values.unlink()

