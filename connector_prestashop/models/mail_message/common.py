# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import fields, models

from ...backend import prestashop
from ...unit.backend_adapter import GenericAdapter

_logger = logging.getLogger(__name__)


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


@prestashop
class MailMessageAdapter(GenericAdapter):
    _model_name = 'prestashop.mail.message'
    _prestashop_model = 'messages'
