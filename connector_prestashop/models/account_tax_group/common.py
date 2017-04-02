# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models

from ...backend import prestashop
from ...unit.backend_adapter import GenericAdapter


class PrestashopAccountTaxGroup(models.Model):
    _name = 'prestashop.account.tax.group'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'account.tax.group': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='account.tax.group',
        string='Tax Group',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.account.tax.group',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
        readonly=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        required=True,
        string='Company',
    )


@prestashop
class TaxGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.account.tax.group'
    _prestashop_model = 'tax_rule_groups'
