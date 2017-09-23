# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.component.core import Component


class MailMessage(models.Model):
    _inherit = 'mail.message'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.mail.message',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopMailMessage(models.Model):
    _name = "prestashop.mail.message"
    _inherit = "prestashop.binding.odoo"
    _inherits = {'mail.message': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='mail.message',
        required=True,
        ondelete='cascade',
        string='Message',
        oldname='openerp_id',
    )


class MailMessageAdapter(Component):
    _name = 'prestashop.mail.message.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.mail.message'

    _model_name = 'prestashop.mail.message'

    @property
    def _prestashop_model(self):
        return self.backend_record.get_version_ps_key('messages')
