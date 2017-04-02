# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp.addons.connector.unit.mapper import (
    mapping,
)
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.models.product_template import \
    importer

_logger = logging.getLogger(__name__)


@prestashop(replacing=importer.FeaturesProductImportMapper)
class FeaturesImportMapper(importer.FeaturesProductImportMapper):

    @mapping
    def extras_features(self, record):
        custom_info_template = self.env.ref(
            'connector_prestashop_feature.tpl_prestashop_features')
        return {'custom_info_template_id': custom_info_template.id}


@prestashop(replacing=importer.ProductTemplateImporter)
class TemplateRecordImportFeatures(importer.ProductTemplateImporter):

    def _import_features(self):
        record = self.prestashop_record
        features = record['associations'].get('product_features', {}).get(
            self.backend_record.get_version_ps_key('product_features'), [])
        if not isinstance(features, list):
            features = [features]
        if not features:
            return
        for feature in features:
            self._import_dependency(
                feature['id'], 'prestashop.product.features')

    def _import_dependencies(self):
        super(TemplateRecordImportFeatures, self)._import_dependencies()
        self._import_features()

    def _product_feature_values_link(self, binding):
        feature_values = self.prestashop_record.get('associations', {}) \
            .get('product_features', {}).get(
            self.backend_record.get_version_ps_key('product_features'), [])
        if not isinstance(feature_values, list):
            feature_values = [feature_values]

        CustomInfoValue = self.session.env['custom.info.value']
        property_binder = self.binder_for('prestashop.product.features')
        option_binder = self.binder_for('prestashop.product.feature.values')

        info_value_domain = [
            ('model', '=', 'product.template'),
            ('res_id', '=', binding.odoo_id.id),
        ]
        initial_info_value = CustomInfoValue.search(info_value_domain)

        properties = []
        for feature_value in feature_values:
            properties.append(
                property_binder.to_odoo(feature_value['id'], unwrap=True).id)

        if properties:
            info_value_domain.append(('property_id', 'in', properties))
        ps_info_values = CustomInfoValue.search(info_value_domain)
        empty_property_value = initial_info_value - ps_info_values
        if empty_property_value:
            empty_property_value.with_context(
                connector_no_export=True).write({'value_id': False})

        for feature_value in feature_values:
            info_property = property_binder.to_odoo(
                feature_value['id'], unwrap=True)
            info_value = option_binder.to_odoo(
                feature_value['id_feature_value'], unwrap=True)
            value_to_update = ps_info_values.filtered(
                lambda x: x.property_id == info_property)
            if value_to_update and value_to_update.value_id != info_value:
                value_to_update.with_context(
                    connector_no_export=True).value_id = info_value

    def _after_import(self, binding):
        super(TemplateRecordImportFeatures, self)._after_import(binding)
        self._product_feature_values_link(binding)
