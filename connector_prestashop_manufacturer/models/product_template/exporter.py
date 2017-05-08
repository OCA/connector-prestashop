# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop_catalog_manager\
    .models.product_template import exporter


@prestashop(replacing=exporter.ManufacturerExportMapper)
class ProductTemplateExportMapper(exporter.ManufacturerExportMapper):
    _model_name = 'prestashop.product.template'

    @mapping
    def manufacturer(self, record):
        if record.manufacturer:
            binder = self.binder_for('prestashop.manufacturer')
            value = binder.to_backend(record.manufacturer.id, wrap=True)
            if value:
                return {'id_manufacturer': value}
        return {}


@prestashop(replacing=exporter.ProductTemplateExporter)
class ProductTemplateExporter(exporter.ProductTemplateExporter):

    def _export_manufacturer(self):
        record = self.binding.manufacturer
        if record:
            # TODO: can't we use ManufacturerExporter right away?
            manuf_binding = self._export_dependency(
                record, 'prestashop.manufacturer')
            # PS needs an address anyway
            addresses = record.child_ids or [record, ]
            for address in addresses:
                self._export_dependency(
                    address,
                    'prestashop.manufacturer.address',
                    bind_values={'prestashop_partner_id': manuf_binding.id})

    def _export_dependencies(self):
        super(ProductTemplateExporter, self)._export_dependencies()
        self._export_manufacturer()
