# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp.addons.connector.unit.mapper import (
    mapping,
    backend_to_m2o,
    ImportMapper,
)
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop_catalog_manager import product
from ..custom_info_option import exporter

_logger = logging.getLogger(__name__)


@prestashop(replacing=product.ProductTemplateExport)
class ProductFeaturesExporter(product.ProductTemplateExport):

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

    def _after_export(self, binding):
        super(ProductFeaturesExporter, self)._after_export(binding)
        # self._product_feature_values_link(binding)


@prestashop(replacing=product.ProductTemplateExportMapper)
class ProductFeaturesExportMapper(product.ProductTemplateExportMapper):
    
    @mapping
    def associations(self, record):
        res = super(ProductFeaturesExportMapper, self).associations(record)
        # Add features in associations key
        return res