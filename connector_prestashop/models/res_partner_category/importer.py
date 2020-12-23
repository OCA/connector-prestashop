# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class PartnerCategoryBatchImporter(Component):
    _name = "prestashop.res.partner.category.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.res.partner.category"


class PartnerCategoryImportMapper(Component):
    _name = "prestashop.res.partner.category.import.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.res.partner.category"

    direct = [
        ("name", "name"),
        ("date_add", "date_add"),
        ("date_upd", "date_upd"),
    ]

    @mapping
    def prestashop_id(self, record):
        return {"prestashop_id": record["id"]}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}


class PartnerCategoryImporter(Component):
    """ Import one translatable record """

    _name = "prestashop.res.partner.category.importer"
    _inherit = "prestashop.translatable.record.importer"
    _apply_on = "prestashop.res.partner.category"
    _translatable_fields = {
        "prestashop.res.partner.category": ["name"],
    }

    def _after_import(self, binding):
        super(PartnerCategoryImporter, self)._after_import(binding)
        record = self.prestashop_record
        if float(record["reduction"]):
            self.env["prestashop.groups.pricelist"].import_record(
                self.backend_record, record["id"]
            )
