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
from openerp.addons.connector_prestashop.models.product_template import \
    importer

_logger = logging.getLogger(__name__)


# @prestashop(replacing=importer.ProductFeaturesImportMapper)
# class ProductFeaturesImportMapper(importer.ProductFeaturesImportMapper):
#     _model_name = 'prestashop.product.template'
#
#     @mapping
#     def extra_features(self, record):
#         mapping_func = backend_to_m2o(
#             'id_manufacturer', binding='prestashop.manufacturer')
#         value = mapping_func(self, record, 'manufacturer')
#         return {'manufacturer': value}


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
            # self._import_dependency(
            #     feature['id'], 'prestashop.product.features')
            self._import_dependency(
                feature['id'], 'prestashop.product.feature.value')

    def _import_dependencies(self):
        super(TemplateRecordImportFeatures, self)._import_dependencies()
        self._import_features()
