# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentMethodImporter(Component):
    _name = "account.payment.method.line.importer"
    _inherit = "prestashop.direct.batch.importer"
    _apply_on = "account.payment.method.line"

    def run(self, filters=None, **kwargs):
        if filters is None:
            filters = {}
        filters["display"] = "[id,payment]"
        return super().run(filters, **kwargs)

    def _import_record(self, record):
        ids = self.env["account.payment.method.line"].search(
            [
                ("name", "=", record["payment"]),
                ("company_id", "=", self.backend_record.company_id.id),
            ]
        )
        if ids:
            return
        self.env["account.payment.method.line"].create(
            {
                "name": record["payment"],
                "company_id": self.backend_record.company_id.id,
            }
        )
