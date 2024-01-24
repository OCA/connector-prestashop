# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.component.core import Component


class AccountMove(models.Model):
    _inherit = "account.move"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.refund",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )

    def action_post(self):
        so_obj = self.env["prestashop.sale.order"]
        line_replacement = {}
        for move in self:
            if move.move_type != "out_invoice":
                continue
            sale_order = so_obj.search([("name", "=", move.invoice_origin)])
            if not sale_order:
                continue
            sale_order = sale_order[0]
            discount_product_id = sale_order.backend_id.discount_product_id.id
            for invoice_line in move.invoice_line_ids:
                if invoice_line.product_id.id != discount_product_id:
                    continue
                amount = invoice_line.price_subtotal
                partner = move.partner_id.commercial_partner_id
                refund = self._find_refund(-1 * amount, partner)
                if refund:
                    invoice_line.unlink()
                    line_replacement[move] = refund
        result = super().action_post()
        # reconcile invoice with refund
        for invoice, refund in line_replacement.items():
            self._reconcile_invoice_refund(invoice, refund)
        return result

    @api.model
    def _reconcile_invoice_refund(self, invoice, refund):
        move_line_obj = self.env["account.move.line"]
        move_lines = move_line_obj.search(
            [
                ("move_id", "=", invoice.id),
                ("debit", "!=", 0.0),
            ]
        )
        move_lines += move_line_obj.search(
            [
                ("move_id", "=", refund.id),
                ("credit", "!=", 0.0),
            ]
        )
        move_lines.reconcile()

    @api.model
    def _find_refund(self, amount, partner):
        records = self.search(
            [
                ("amount_untaxed", "=", amount),
                ("move_type", "=", "out_refund"),
                ("state", "=", "open"),
                ("partner_id", "=", partner.id),
            ]
        )
        return records[:1].id


class PrestashopRefund(models.Model):
    _name = "prestashop.refund"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"account.move": "odoo_id"}
    _description = "Refund Prestshop Bindings"

    odoo_id = fields.Many2one(
        comodel_name="account.move",
        required=True,
        ondelete="cascade",
        string="Invoice",
    )

    def import_refunds(self, backend, since_date, **kwargs):
        filters = None
        if since_date:
            filters = {"date": "1", "filter[date_upd]": ">[%s]" % (since_date)}
        now_fmt = fields.Datetime.now()
        self.env["prestashop.refund"].with_delay().import_batch(
            backend, filters, **kwargs
        )
        backend.import_refunds_since = now_fmt
        return True


class RefundAdapter(Component):
    _name = "prestashop.refund.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.refund"

    @property
    def _prestashop_model(self):
        return self.backend_record.get_version_ps_key("order_slip")
