# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentMethodImporter(Component):
    _name = "payment.method.importer"
    _inherit = "prestashop.direct.batch.importer"
    _apply_on = "payment.method"

    def run(self, filters=None, **kwargs):
        if filters is None:
            filters = {}
        filters["display"] = "[id,payment]"
        return super(PaymentMethodImporter, self).run(filters, **kwargs)

    def _import_record(self, record):
        ids = self.env["payment.method"].search(
            [
                ("name", "=", record["payment"]),
                ("company_id", "=", self.backend_record.company_id.id),
            ]
        )
        if ids:
            return
        self.env["payment.method"].create(
            {
                "name": record["payment"],
                "company_id": self.backend_record.company_id.id,
            }
        )
