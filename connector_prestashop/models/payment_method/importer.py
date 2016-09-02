# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from ...unit.importer import BatchImporter
from ...backend import prestashop


@prestashop
class PaymentMethodBatchImporter(BatchImporter):
    _model_name = 'payment.method'

    def run(self, filters=None, **kwargs):
        if filters is None:
            filters = {}
        filters['display'] = '[id,payment]'
        return super(PaymentMethodBatchImporter, self).run(
            filters, **kwargs
        )

    def _import_record(self, record):
        ids = self.env['payment.method'].search([
            ('name', '=', record['payment']),
            ('company_id', '=', self.backend_record.company_id.id),
        ])
        if ids:
            return
        self.env['payment.method'].create({
            'name': record['payment'],
            'company_id': self.backend_record.company_id.id,
        })
