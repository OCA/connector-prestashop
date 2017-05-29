# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


class PrestashopAccountTax(models.Model):
    _name = 'prestashop.account.tax'
    # Do not inherit from `prestashop.binding.odoo`
    # because we do not want the constraint `prestashop_erp_uniq`.
    # This allows us to create duplicated taxes.
    _inherit = 'prestashop.binding'
    _inherits = {'account.tax': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )


class AccountTax(models.Model):
    _inherit = 'account.tax'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.account.tax',
        inverse_name='odoo_id',
        string='prestashop Bindings',
        readonly=True,
    )


@prestashop
class AccountTaxAdapter(GenericAdapter):
    _model_name = 'prestashop.account.tax'
    _prestashop_model = 'taxes'
