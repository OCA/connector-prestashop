# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector.components.mapper import mapping
from odoo.addons.component.core import Component
from ...backend import prestashop


@prestashop
class ProductPricelistMapper(Component):
    _name = 'prestashop.groups.pricelist.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.groups.pricelist'

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
class ProductPricelistImporter(Component):
    _name = 'prestashop.groups.pricelist.importer'
    _inherit = 'prestashop.translatable.record.importer'
    _apply_on = 'prestashop.groups.pricelist'

    _translatable_fields = {
        'prestashop.groups.pricelist': ['name'],
    }
