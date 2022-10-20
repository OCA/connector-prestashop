# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime

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
    ]

    @mapping
    def date_add(self, record):
        if record["date_add"] == "0000-00-00 00:00:00":
            return {"date_add": datetime.datetime.now()}
        return {"date_add": record["date_add"]}

    @mapping
    def date_upd(self, record):
        if record["date_upd"] == "0000-00-00 00:00:00":
            return {"date_upd": datetime.datetime.now()}
        return {"date_upd": record["date_upd"]}

    @mapping
    def prestashop_id(self, record):
        return {"prestashop_id": record["id"]}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}


class PartnerCategoryImporter(Component):
    """Import one translatable record"""

    _name = "prestashop.res.partner.category.importer"
    _inherit = "prestashop.translatable.record.importer"
    _apply_on = "prestashop.res.partner.category"
    _translatable_fields = {
        "prestashop.res.partner.category": ["name"],
    }

    def _after_import(self, binding):
        res = super()._after_import(binding)
        record = self.prestashop_record
        if float(record["reduction"]):
            self.env["prestashop.groups.pricelist"].import_record(
                self.backend_record, record["id"]
            )
        return res
