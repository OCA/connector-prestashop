# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector.unit.mapper import ImportMapper, mapping
from ...components.importer import PrestashopImporter, DirectBatchImporter
from odoo.addons.connector.unit.mapper import external_to_m2o
from ...backend import prestashop


@prestashop
class ShopImportMapper(ImportMapper):
    _model_name = 'prestashop.shop'

    direct = [
        ('name', 'name'),
        (external_to_m2o('id_shop_group'), 'shop_group_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def warehouse_id(self, record):
        return {'warehouse_id': self.backend_record.warehouse_id.id}

    @mapping
    def opener_id(self, record):
        return {'odoo_id': self.backend_record.warehouse_id.id}


@prestashop
class ShopImporter(PrestashopImporter):
    _model_name = 'prestashop.shop'


@prestashop
class ShopBatchImporter(DirectBatchImporter):
    _model_name = 'prestashop.shop'
