# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.refund',
        inverse_name='openerp_id',
        string='PrestaShop Bindings'
    )

    def action_move_create(self):
        so_obj = self.env['prestashop.sale.order']
        line_replacement = {}
        for invoice in self:
            sale_order = so_obj.search([('name', '=', invoice.origin)])
            if not sale_order:
                continue
            sale_order = sale_order[0]
            discount_product_id = sale_order.backend_id.discount_product_id.id

            for invoice_line in invoice.invoice_line:
                if invoice_line.product_id.id != discount_product_id:
                    continue
                amount = invoice_line.price_subtotal
                partner_id = invoice.partner_id.commercial_partner_id.id
                refund_id = self._find_refund(-1 * amount, partner_id)
                if refund_id:
                    invoice_line.unlink()
                    line_replacement[invoice.id] = refund_id
                    invoice.button_reset_taxes()

        result = super(AccountInvoice, self).action_move_create()
        # reconcile invoice with refund
        for invoice_id, refund_id in line_replacement.items():
            self._reconcile_invoice_refund(invoice_id, refund_id)
        return result

    def _reconcile_invoice_refund(self, cr, uid, invoice_id, refund_id,
                                  context=None):
        move_line_obj = self.pool.get('account.move.line')
        invoice_obj = self.pool.get('account.invoice')

        invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
        refund = invoice_obj.browse(cr, uid, refund_id, context=context)

        move_line_ids = move_line_obj.search(cr, uid, [
            ('move_id', '=', invoice.move_id.id),
            ('debit', '!=', 0.0),
        ], context=context)
        move_line_ids += move_line_obj.search(cr, uid, [
            ('move_id', '=', refund.move_id.id),
            ('credit', '!=', 0.0),
        ], context=context)
        move_line_obj.reconcile_partial(
            cr, uid, move_line_ids, context=context
        )

    def _find_refund(self, cr, uid, amount, partner_id, context=None):
        ids = self.search(cr, uid, [
            ('amount_untaxed', '=', amount),
            ('type', '=', 'out_refund'),
            ('state', '=', 'open'),
            ('partner_id', '=', partner_id),
        ])
        if not ids:
            return None
        return ids[0]


class PrestashopRefund(models.Model):
    _name = 'prestashop.refund'
    _inherit = 'prestashop.binding'
    _inherits = {'account.invoice': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='account.invoice',
        required=True,
        ondelete='cascade',
        string='Invoice',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
    ]
