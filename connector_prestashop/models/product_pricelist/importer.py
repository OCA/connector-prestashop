# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from ...backend import prestashop
from ...unit.importer import TranslatableRecordImporter
from openerp.addons.connector.unit.mapper import (
    ImportMapper, mapping, only_create
)


@prestashop
class ProductPricelistMapper(ImportMapper):
    _model_name = 'prestashop.groups.pricelist'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def static(self, record):
        return {'active': True, 'type': 'sale'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    @only_create
    def versions(self, record):
        item = {
            'min_quantity': 0,
            'sequence': 5,
            'base': 1,
            'price_discount': - float(record['reduction']) / 100.0,
        }
        version = {
            'name': 'Version',
            'active': True,
            'items_id': [(0, 0, item)],
        }
        return {'version_id': [(0, 0, version)]}


@prestashop
class ProductPricelistImport(TranslatableRecordImporter):
    _model_name = [
        'prestashop.groups.pricelist',
    ]

    _translatable_fields = {
        'prestashop.groups.pricelist': ['name'],
    }

    def _run_record(self, prestashop_record, lang_code, erp_id=None):
        return super(ProductPricelistImport, self)._run_record(
            prestashop_record, lang_code, erp_id=erp_id
        )
