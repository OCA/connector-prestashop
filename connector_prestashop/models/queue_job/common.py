# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions, api, models

class QueueJob(models.Model):
    _inherit = 'queue.job'

    @api.multi
    def related_action_record(self, binding_id_pos=0):
        self.ensure_one()

        model_name = self.model_name
        binding_id = self.args[binding_id_pos]
        record = self.env[binding_model].browse(binding_id)
        odoo_name = record.odoo_id._name

        action = {
            'name': _(odoo_name),
            'type': 'ir.actions.act_window',
            'res_model': odoo_name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': record.odoo_id.id,
        }
        return action
