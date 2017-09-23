# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector.unit.mapper import (
    ImportMapper,
    mapping,
)
from ...components.importer import TranslatableRecordImporter
from ...backend import prestashop


@prestashop
class ProductPricelistMapper(ImportMapper):
    _model_name = 'prestashop.groups.pricelist'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def static(self, record):
        return {'active': True}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def versions(self, record):
        item = {
            'min_quantity': 0,
            'sequence': 5,
            'base': 'list_price',
            'compute_price': 'percentage',
            'percent_price': float(record['reduction']),
        }
        return {'item_ids': [(5,), (0, 0, item)]}


@prestashop
class ProductPricelistImporter(TranslatableRecordImporter):
    _model_name = [
        'prestashop.groups.pricelist',
    ]

    _translatable_fields = {
        'prestashop.groups.pricelist': ['name'],
    }
