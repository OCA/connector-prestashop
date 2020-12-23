# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class MailMessageMapper(Component):
    _name = "prestashop.mail.message.import.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.mail.message"

    _model_name = "prestashop.mail.message"

    direct = [
        ("message", "body"),
    ]

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def type(self, record):
        return {"type": "comment"}

    @mapping
    def object_ref(self, record):
        binder = self.binder_for("prestashop.sale.order")
        order = binder.to_internal(record["id_order"], unwrap=True)
        return {
            "model": "sale.order",
            "res_id": order.id,
        }

    @mapping
    def author_id(self, record):
        if record["id_customer"] != "0":
            binder = self.binder_for("prestashop.res.partner")
            partner = binder.to_internal(record["id_customer"], unwrap=True)
            return {"author_id": partner.id}
        return {}


class MailMessageImporter(Component):
    """ Import one simple record """

    _name = "prestashop.mail.message.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.mail.message"

    _model_name = "prestashop.mail.message"

    def _import_dependencies(self):
        record = self.prestashop_record
        self._import_dependency(record["id_order"], "prestashop.sale.order")
        if record["id_customer"] != "0":
            self._import_dependency(record["id_customer"], "prestashop.res.partner")

    def _has_to_skip(self):
        record = self.prestashop_record
        if not record.get("id_order"):
            return "no id_order"
        binder = self.binder_for("prestashop.sale.order")
        order_binding = binder.to_internal(record["id_order"])
        return record["id_order"] == "0" or not order_binding


class MailMessageBatchImporter(Component):
    _name = "prestashop.mail.message.delayed.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.mail.message"

    _model_name = "prestashop.mail.message"
