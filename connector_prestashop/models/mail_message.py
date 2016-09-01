# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class MailMessage(models.Model):
    _inherit = 'mail.message'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.mail.message',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
    )


class PrestashopMailMessage(models.Model):
    _name = "prestashop.mail.message"
    _inherit = "prestashop.binding"
    _inherits = {'mail.message': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='mail.message',
        required=True,
        ondelete='cascade',
        string='Message',
    )
