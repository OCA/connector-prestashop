# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _
from openerp.addons.connector.unit.mapper import ImportMapper, mapping
from ...unit.importer import PrestashopImporter, DirectBatchImporter
from ...backend import prestashop


@prestashop
class ShopGroupImportMapper(ImportMapper):
    _model_name = 'prestashop.shop.group'

    direct = [('name', 'name')]

    @mapping
    def name(self, record):
        name = record['name']
        if name is None:
            name = _('Undefined')
        return {'name': name}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class ShopGroupImporter(PrestashopImporter):
    _model_name = 'prestashop.shop.group'


@prestashop
class ShopGroupBatchImporter(DirectBatchImporter):
    _model_name = 'prestashop.shop.group'
