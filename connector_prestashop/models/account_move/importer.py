# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError


class RefundImporter(Component):
    _name = "prestashop.refund.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.refund"

    _model_name = "prestashop.refund"

    def _import_dependencies(self):
        record = self.prestashop_record
        self._import_dependency(record["id_customer"], "prestashop.res.partner")
        self._import_dependency(record["id_order"], "prestashop.sale.order")

    def _open_refund(self, binding):
        invoice = binding.odoo_id
        if invoice.amount_total == (
            float(self.prestashop_record["amount"])
            + float(self.prestashop_record["shipping_cost_amount"])
        ):
            invoice.action_post()
        # TODO else add activity to warn about differnt amount

    #        else:
    #            message=_(
    #                "The refund for order %s has a different amount "
    #                "in PrestaShop and in Odoo."
    #            )
    #            % invoice.origin,

    def _after_import(self, binding):
        super()._after_import(binding)
        self._open_refund(binding)

    def _has_to_skip(self, binding=False):
        """Return True if the import can be skipped"""
        if binding:
            return True


class RefundMapper(Component):
    _name = "prestashop.refund.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.refund"

    direct = [
        ("id", "ref"),
        ("date_add", "invoice_date"),
    ]

    @mapping
    def journal(self, record):
        journal = self.backend_record.refund_journal_id
        if not journal:
            raise MappingError(
                _("The refund journal must be configured on the PrestaShop Backend.")
            )
        return {"journal_id": journal.id}

    def _get_order(self, record):
        binder = self.binder_for("prestashop.sale.order")
        return binder.to_internal(record["id_order"])

    @mapping
    def from_sale_order(self, record):
        sale_order = self._get_order(record)
        fiscal_position = None
        if sale_order.fiscal_position_id:
            fiscal_position = sale_order.fiscal_position_id.id
        if sale_order:
            partner = sale_order.partner_invoice_id
        else:
            binder = self.binder_for("prestashop.res.partner")
            partner = binder.to_internal(record["id_customer"], unwrap=True)
        return {
            "invoice_origin": sale_order["name"],
            "fiscal_position_id": fiscal_position,
            "partner_id": partner.id,
        }

    # TODO maybe add a mail_message after_import?
    # but comment does not exist anymore and narration is not the good field for this
    # as it appear on invoice PDF
    #    @mapping
    #    def comment(self, record):
    #        return {"comment": _("PrestaShop amount: %s") % record["amount"]}

    @mapping
    @only_create
    def invoice_lines(self, record):
        slip_details = (
            record.get("associations", {})
            .get("order_slip_details", [])
            .get(self.backend_record.get_version_ps_key("order_slip_detail"), [])
        )
        if isinstance(slip_details, dict):
            slip_details = [slip_details]
        lines = []
        order_binding = self._get_order(record)
        fpos = order_binding.fiscal_position_id
        shipping_line = self._invoice_line_shipping(record, fpos)
        if shipping_line:
            lines.append((0, 0, shipping_line))
        for slip_detail in slip_details:
            line = self._invoice_line(slip_detail, fpos)
            if line:
                lines.append((0, 0, line))
        return {"invoice_line_ids": lines}

    def _invoice_line_shipping(self, record, fpos):
        order_line = self._get_shipping_order_line(record)
        if not order_line:
            return None
        if isinstance(order_line, list):
            order_line = order_line[0]
        if not record["shipping_cost"] == "1":
            return None
        if self.backend_record.taxes_included:
            price_unit = record["total_shipping_tax_incl"]
        else:
            price_unit = record["total_shipping_tax_excl"]
        if price_unit in [0.0, "0.00"]:
            return None
        product = order_line.product_id
        account = product.property_account_income_id
        if not account:
            account = product.categ_id.property_account_income_categ_id
        if fpos:
            account = fpos.map_account(account)
        return {
            "quantity": 1,
            "product_id": product.id,
            "name": order_line.name,
            "tax_ids": [(6, 0, order_line.tax_id.ids)],
            "price_unit": price_unit,
            "discount": order_line.discount,
            "account_id": account.id,
        }

    def _get_shipping_order_line(self, record):
        binder = self.binder_for("prestashop.sale.order")
        sale_order = binder.to_internal(record["id_order"], unwrap=True)
        if not sale_order.carrier_id:
            return None
        sale_order_lines = self.env["sale.order.line"].search(
            [
                ("order_id", "=", sale_order.id),
                ("is_delivery", "=", True),
            ]
        )
        if not sale_order_lines:
            return None
        return sale_order_lines[0]

    def _invoice_line(self, record, fpos):
        order_line = self._get_order_line(record["id_order_detail"])
        tax_ids = []
        if order_line is None:
            product_id = None
            name = "Order line not found"
            account = self.env["account.account"]
        else:
            product = order_line.product_id
            product_id = product.id
            name = order_line.name
            for tax in order_line.tax_id:
                tax_ids.append(tax.id)
            account = product.property_account_income_id
            if not account:
                categ = product.categ_id
                account = categ.property_account_income_categ_id
        if fpos and account:
            account = fpos.map_account(account)
        if record["product_quantity"] == "0":
            quantity = 1
        else:
            quantity = record["product_quantity"]

        if self.backend_record.taxes_included:
            price_unit = record["amount_tax_incl"]
        else:
            price_unit = record["amount_tax_excl"]

        try:
            price_unit = float(price_unit) / float(quantity)
        except ValueError:
            pass

        discount = False
        if price_unit in ["0.00", ""] and order_line is not None:
            price_unit = order_line["price_unit"]
            discount = order_line["discount"]
        return {
            "quantity": quantity,
            "product_id": product_id,
            "name": name,
            "tax_ids": [(6, 0, tax_ids)],
            "price_unit": price_unit,
            "discount": discount,
            "account_id": account.id,
        }

    def _get_order_line(self, order_details_id):
        order_line = self.env["prestashop.sale.order.line"].search(
            [
                ("prestashop_id", "=", order_details_id),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        if not order_line:
            return None
        return order_line.with_context(company_id=self.backend_record.company_id.id)

    @mapping
    def move_type(self, record):
        return {"move_type": "out_refund"}

    @mapping
    def company_id(self, record):
        return {"company_id": self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}


class RefundBatchImporter(Component):
    _name = "prestashop.refund.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.refund"
