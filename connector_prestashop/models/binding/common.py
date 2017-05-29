# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.queue_job.job import job
from ...unit.importer import PrestashopImporter, BatchImporter
from ...unit.importer import import_record


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
    def import_record(self, backend, prestashop_id, **kwargs):
        """ Import a record from PrestaShop """
        env = backend.get_environment(self._name)
        importer = env.get_connector_unit(PrestashopImporter)
        return importer.run(prestashop_id, **kwargs)

    @job(default_channel='root.prestashop')
    def import_batch(self, backend=None, filters=None, **kwargs):
        """ Prepare a batch import of records from PrestaShop """
        env = backend.get_environment(self._name)
        importer = env.get_connector_unit(BatchImporter)
        return importer.run(filters=filters, **kwargs)

    @api.multi
    def resync(self):
        func = import_record
        if self.env.context.get('connector_delay'):
            func = import_record.delay
        for record in self:
            func(self.env, self._name, record.backend_id.id,
                 record.prestashop_id)
        return True
