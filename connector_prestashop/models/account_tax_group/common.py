# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.addons.component.core import Component


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
        string='Company',
    )
    tax_ids = fields.One2many(
        comodel_name='account.tax',
        inverse_name='tax_group_id',
        string='Taxes',
    )


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


class TaxGroupAdapter(Component):
    _name = 'prestashop.account.tax.group.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.account.tax.group'

    _model_name = 'prestashop.account.tax.group'
    _prestashop_model = 'tax_rule_groups'
