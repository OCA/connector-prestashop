# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.connector_prestashop.unit.exporter import (
    PrestashopExporter,
    export_record,
    TranslationPrestashopExporter,
)
from openerp.addons.connector_prestashop.unit.mapper import (
    TranslationPrestashopExportMapper,
    PrestashopExportMapper
)
from ..custom_info_property import exporter
from openerp.addons.connector_prestashop.backend import prestashop


@prestashop
class ProductFeatureValuesExporter(PrestashopExporter):
    _model_name = 'prestashop.product.feature.values'

    def _create(self, record):
        res = super(ProductFeatureValuesExporter, self)._create(record)
        return res['prestashop']['id_value']['id']
    
    def _export_dependencies(self):
        """ Export the dependencies for the product features"""
        ps_template = self.env.ref(
            'connector_prestashop_feature.tpl_prestashop_features')
        for property_value in self.binding:
            property = property_value.property_ids.filtered(
                lambda x: x.template_id == ps_template)
            self._export_dependency(
                property, 'prestashop.product.features',
                exporter_class=exporter.ProductFeaturesExporter)


@prestashop
class ProductFeatureValuesExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.product.feature.values'

    direct = [
        ('name', 'value'),
    ]

    @mapping
    def position(self, record):
        return {}
