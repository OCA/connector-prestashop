# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.queue_job.job import job
from ...components.importer import import_record


class PrestashopBinding(models.AbstractModel):
    _name = 'prestashop.binding'
    _inherit = 'external.binding'
    _description = 'PrestaShop Binding (abstract)'

    # 'openerp_id': openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        required=True,
        ondelete='restrict'
    )
    prestashop_id = fields.Integer('ID on PrestaShop')

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A record with same ID on PrestaShop already exists.'),
    ]

    @job(default_channel='root.prestashop')
    @api.model
    def import_record(self, backend, prestashop_id, force=False):
        """ Import a record from PrestaShop """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(prestashop_id, force=force)

    @job(default_channel='root.prestashop')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare a batch import of records from PrestaShop """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.prestashop')
    @api.multi
    def export_record(self, fields=None):
        """ Export a record on Magento """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

    @job(default_channel='root.prestashop')
    def export_delete_record(self, backend, external_id):
        """ Delete a record on Magento """
        with backend.work_on(self._name) as work:
            deleter = work.component(usage='record.exporter.deleter')
            return deleter.run(external_id)

    #TODO: Research
    @api.multi
    def resync(self):
        func = import_record
        if self.env.context.get('connector_delay'):
            func = import_record.delay
        for record in self:
            func(self.env, self._name, record.backend_id.id,
                 record.prestashop_id)
        return True
