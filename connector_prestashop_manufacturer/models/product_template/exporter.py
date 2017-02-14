# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector.unit.mapper import m2o_to_backend

from openerp.addons.connector_prestashop.backend import prestashop

from openerp.addons.connector_prestashop_catalog_manager\
    .models.product_template import exporter


@prestashop(replacing=exporter.ManufacturerExportMapper)
class ProductTemplateExportMapper(exporter.ManufacturerExportMapper):
    _model_name = 'prestashop.product.template'

    @mapping
    def manufacturer(self, record):
        mapping_func = m2o_to_backend(
            'manufacturer', binding='prestashop.manufacturer')
        value = mapping_func(self, record, 'manufacturer')
        return {'id_manufacturer': value}


@prestashop(replacing=exporter.ProductTemplateExporter)
class ProductTemplateExporter(exporter.ProductTemplateExporter):

    def _export_manufacturer(self):
        record = self.binding.manufacturer
        if record:
            manuf_binding = self._export_dependency(
                record, 'prestashop.manufacturer')
            for address in record.child_ids:
                self._export_dependency(
                    address,
                    'prestashop.manufacturer.address',
                    bind_values={'prestashop_partner_id': manuf_binding.id})

    def _export_dependencies(self):
        super(ProductTemplateExporter, self)._export_dependencies()
        self._export_manufacturer()
