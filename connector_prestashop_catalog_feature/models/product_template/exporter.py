# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop_catalog_manager.models.\
    product_template import exporter as product_exporter
from ..custom_info_option import exporter

_logger = logging.getLogger(__name__)


@prestashop(replacing=product_exporter.ProductTemplateExport)
class ProductFeaturesExporter(product_exporter.ProductTemplateExport):

    def _export_features(self):
        ps_template = self.env.ref(
            'connector_prestashop_feature.tpl_prestashop_features')
        if not self.binding.custom_info_template_id == ps_template:
            return

        for info_value in self.binding.custom_info_ids:
            if not info_value.value_id.prestashop_bind_ids:
                self._export_dependency(
                    info_value.value_id, 'prestashop.product.feature.values',
                    exporter_class=exporter.ProductFeatureValuesExporter)

    def _export_dependencies(self):
        super(ProductFeaturesExporter, self)._export_dependencies()
        self._export_features()


@prestashop(replacing=product_exporter.ProductTemplateExportMapper)
class ProductFeaturesExportMapper(
    product_exporter.ProductTemplateExportMapper):

    @mapping
    def associations(self, record):
        res = super(ProductFeaturesExportMapper, self).associations(record)
        # Add features in associations key
        feature_binder = self.binder_for('prestashop.product.features')
        feature_value_binder = self.binder_for(
            'prestashop.product.feature.values')
        feature_values = []
        for custom_info_value in record.custom_info_ids:
            if custom_info_value.value_id:
                feature = custom_info_value.property_id
                ps_feature_id = feature_binder.to_backend(
                    feature.id, wrap=True)
                ps_feature_value_id = feature_value_binder.to_backend(
                    custom_info_value.value_id.id, wrap=True)
                feature_values.append({
                    'id': ps_feature_id,
                    'id_feature_value': ps_feature_value_id,
                })
        features = {
            'product_features': {'product_feature': feature_values},
        }
        res['associations'].update(features)
        return res
