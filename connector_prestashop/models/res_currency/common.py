# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class PrestashopResCurrency(models.Model):
    _name = 'prestashop.res.currency'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'res.currency': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.currency',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
        readonly=True
    )


class ResCurrencyAdapter(Component):
    _name = 'prestashop.res.currency.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.res.currency'
    _prestashop_model = 'currencies'
