# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.unit.mapper import ImportMapper, mapping
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


@prestashop
class TaxGroupImporter(PrestashopImporter):
    _model_name = 'prestashop.account.tax.group'


@prestashop
class TaxGroupBatchImporter(DirectBatchImporter):
    _model_name = 'prestashop.account.tax.group'
