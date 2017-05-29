# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector.unit.mapper import ImportMapper, mapping
from ...unit.importer import PrestashopImporter, DelayedBatchImporter
from ...backend import prestashop


@prestashop
class MailMessageMapper(ImportMapper):
    _model_name = 'prestashop.mail.message'

    direct = [
        ('message', 'body'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def type(self, record):
        return {'type': 'comment'}

    @mapping
    def object_ref(self, record):
        binder = self.binder_for('prestashop.sale.order')
        order = binder.to_internal(record['id_order'], unwrap=True)
        return {
            'model': 'sale.order',
            'res_id': order.id,
        }

    @mapping
    def author_id(self, record):
        if record['id_customer'] != '0':
            binder = self.binder_for('prestashop.res.partner')
            partner = binder.to_internal(record['id_customer'], unwrap=True)
            return {'author_id': partner.id}
        return {}


@prestashop
class MailMessageImporter(PrestashopImporter):
    """ Import one simple record """
    _model_name = 'prestashop.mail.message'

    def _import_dependencies(self):
        record = self.prestashop_record
        self._import_dependency(record['id_order'], 'prestashop.sale.order')
        if record['id_customer'] != '0':
            self._import_dependency(
                record['id_customer'], 'prestashop.res.partner'
            )

    def _has_to_skip(self):
        record = self.prestashop_record
        if not record.get('id_order'):
            return 'no id_order'
        binder = self.binder_for('prestashop.sale.order')
        order_binding = binder.to_internal(record['id_order'])
        return record['id_order'] == '0' or not order_binding


@prestashop
class MailMessageBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.mail.message'
