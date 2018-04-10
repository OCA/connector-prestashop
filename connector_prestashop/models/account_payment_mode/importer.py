# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from ...backend import prestashop


# # @prestashop
class PaymentModeBatchImporter(Component):
    _name = 'account.payment.mode.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'account.payment.mode'

    _model_name = 'account.payment.mode'

    def run(self, filters=None, **kwargs):
        if filters is None:
            filters = {}
        filters['display'] = '[id,payment]'
        return super(PaymentModeBatchImporter, self).run(
            filters, **kwargs
        )

    def _import_record(self, record, **kwargs):
        """ Create the missing payment method

        If we have only 1 bank journal, we link the payment method to it,
        otherwise, the user will have to create manually the payment mode.
        """
        if self.binder_for().to_internal(record['payment']):
            return  # already exists
        method_xmlid = 'account.account_payment_method_manual_in'
        payment_method = self.env.ref(method_xmlid, raise_if_not_found=False)
        if not payment_method:
            return
        journals = self.env['account.journal'].search(
            [('type', '=', 'bank'),
             ('company_id', '=', self.backend_record.company_id.id),
             ],
        )
        if len(journals) != 1:
            return
        mode = self.model.create({
            'name': record['payment'],
            'company_id': self.backend_record.company_id.id,
            'bank_account_link': 'fixed',
            'fixed_journal_id': journals.id,
            'payment_method_id': payment_method.id
        })
        self.backend_record.add_checkpoint(mode)
