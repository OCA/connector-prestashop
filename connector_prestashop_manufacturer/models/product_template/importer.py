# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.models.product_template import \
    importer

_logger = logging.getLogger(__name__)


@prestashop(replacing=importer.ManufacturerProductImportMapper)
class ManufacturerImportMapper(importer.ManufacturerProductImportMapper):
    _model_name = 'prestashop.product.template'

    @mapping
    def extras_manufacturer(self, record):
        if record.get('id_manufacturer'):
            binder = self.binder_for('prestashop.res.partner')
            value = binder.to_odoo(record['id_manufacturer'], unwrap=True)
            if value:
                return {'manufacturer': value.id}
        return {}


@prestashop(replacing=importer.ProductTemplateImporter)
class ManufacturerImporter(importer.ProductTemplateImporter):

    def _import_manufacturer(self):
        record = self.prestashop_record
        if int(record['id_manufacturer']):
            self._import_dependency(
                record['id_manufacturer'], 'prestashop.manufacturer')

    def _import_dependencies(self):
        super(ManufacturerImporter, self)._import_dependencies()
        self._import_manufacturer()
