# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.queue_job.job import job, related_action
from ...components.importer import import_record
from odoo.addons.connector.exception import RetryableJobError


class PrestashopBinding(models.AbstractModel):
    _name = 'prestashop.binding'
    _inherit = 'external.binding'
    _description = 'PrestaShop Binding (abstract)'

    # 'odoo_id': openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        required=True,
        ondelete='restrict'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    prestashop_id = fields.Integer('ID on PrestaShop')

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A record with same ID on PrestaShop already exists.'),
    ]

    def check_active(self, backend):
        if not backend.active:
            raise RetryableJobError(
                'Backend %s is inactive please consider changing this'
                'The job will be retried later.' %
                (backend.name,))

        
    @job(default_channel='root.prestashop')
    @api.model
    def import_record(self, backend, prestashop_id, force=False):
        """ Import a record from PrestaShop """
        self.check_active(backend)
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(prestashop_id, force=force)

    @job(default_channel='root.prestashop')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare a batch import of records from PrestaShop """
        self.check_active(backend)
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.prestashop')
    @related_action(action='related_action_record')
    @api.multi
    def export_record(self, fields=None):
        """ Export a record on PrestaShop """
        self.ensure_one()
        self.check_active(backend)
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

    @job(default_channel='root.prestashop')
    def export_delete_record(self, backend, external_id):
        """ Delete a record on PrestaShop """
        self.check_active(backend)
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


class PrestashopBindingOdoo(models.AbstractModel):
    _name = 'prestashop.binding.odoo'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Binding with Odoo binding (abstract)'

    def _get_selection(self):
        records = self.env['ir.model'].search([])
        return [(r.model, r.name) for r in records] + [('', '')]

    # 'odoo_id': odoo-side id must be re-declared in concrete model
    # for having a many2one instead of a reference field
    odoo_id = fields.Reference(
        required=True,
        ondelete='cascade',
        string='Odoo binding',
        selection=_get_selection,
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, odoo_id)',
         'An ERP record with same ID already exists on PrestaShop.'),
    ]
