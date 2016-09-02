# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.account.tax.group',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
        readonly=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        required=True,
        string='Company',
    )
    tax_ids = fields.One2many(
        comodel_name='account.tax',
        inverse_name='tax_group_id',
        string='Taxes',
    )


class PrestashopAccountTaxGroup(models.Model):
    _name = 'prestashop.account.tax.group'
    _inherit = 'prestashop.binding'
    _inherits = {'account.tax.group': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='account.tax.group',
        string='Tax Group',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
    ]


@prestashop
class TaxGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.account.tax.group'
    _prestashop_model = 'tax_rule_groups'
