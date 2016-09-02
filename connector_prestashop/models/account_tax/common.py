# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


class PrestashopAccountTax(models.Model):
    _name = 'prestashop.account.tax'
    _inherit = 'prestashop.binding'
    _inherits = {'account.tax': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax',
        required=True,
        ondelete='cascade'
    )


class AccountTax(models.Model):
    _inherit = 'account.tax'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.account.tax',
        inverse_name='openerp_id',
        string='prestashop Bindings',
        readonly=True,
    )


@prestashop
class AccountTaxAdapter(GenericAdapter):
    _model_name = 'prestashop.account.tax'
    _prestashop_model = 'taxes'
