# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector.components.mapper import mapping
from odoo.addons.component.core import Component
from ...components.importer import import_record
from ...backend import prestashop


@prestashop
class PartnerCategoryImportMapper(Component):
    _name = 'prestashop.res.partner.category.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.res.partner.category'

    direct = [
        ('name', 'name'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
    ]

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class PartnerCategoryImporter(Component):
    """ Import one translatable record """
    _name = 'prestashop.res.partner.category.importer'
    _inherit = 'prestashop.translatable.record.importer'
    _apply_on = 'prestashop.res.partner.category'

    _translatable_fields = {
        'prestashop.res.partner.category': ['name'],
    }

    def _after_import(self, binding):
        super(PartnerCategoryImporter, self)._after_import(binding)
        record = self.prestashop_record
        if float(record['reduction']):
            import_record(
                self.session,
                'prestashop.groups.pricelist',
                self.backend_record.id,
                record['id']
            )


@prestashop
class PartnerCategoryBatchImporter(Component):
    _name = 'prestashop.res.partner.category.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = 'prestashop.res.partner.category'
