# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector.unit.mapper import backend_to_m2o
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.models.product_template import \
    importer

_logger = logging.getLogger(__name__)


@prestashop(replacing=importer.ManufacturerProductImportMapper)
class ManufacturerImportMapper(importer.ManufacturerProductImportMapper):
    _model_name = 'prestashop.product.template'

    @mapping
    def extras_manufacturer(self, record):
        mapping_func = backend_to_m2o(
            'id_manufacturer', binding='prestashop.manufacturer')
        value = mapping_func(self, record, 'manufacturer')
        return {'manufacturer': value}


@prestashop(replacing=importer.ProductTemplateImporter)
class ProductTemplateImporterManufacturer(importer.ProductTemplateImporter):

    def _import_manufacturer(self):
        record = self.prestashop_record
        if int(record['id_manufacturer']):
            self._import_dependency(
                record['id_manufacturer'], 'prestashop.manufacturer')

    def _import_dependencies(self):
        super(ProductTemplateImporterManufacturer, self)._import_dependencies()
        self._import_manufacturer()
