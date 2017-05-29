# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector.unit.mapper import (
    ImportMapper,
    mapping,
    only_create,
)
from ...unit.importer import PrestashopImporter, DirectBatchImporter
from ...backend import prestashop


@prestashop
class TaxGroupMapper(ImportMapper):
    _model_name = 'prestashop.account.tax.group'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @only_create
    @mapping
    def odoo_id(self, record):
        tax_group = self.env['account.tax.group'].search([
            ('name', '=', record['name'])
        ])
        if tax_group:
            return {'odoo_id': tax_group.id}


@prestashop
class TaxGroupImporter(PrestashopImporter):
    _model_name = 'prestashop.account.tax.group'


@prestashop
class TaxGroupBatchImporter(DirectBatchImporter):
    _model_name = 'prestashop.account.tax.group'
