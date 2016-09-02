# -*- coding: utf-8 -*-
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    tax_ids = fields.One2many(
        comodel_name='account.tax',
        inverse_name='tax_group_id',
        string='Taxes',
    )
