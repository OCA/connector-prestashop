# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields
from odoo.addons.component.core import Component
from ...backend import prestashop


class SaleOrderState(models.Model):
    _name = 'sale.order.state'

    name = fields.Char('Name', translate=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
    )
    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order.state',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopSaleOrderState(models.Model):
    _name = 'prestashop.sale.order.state'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order.state': 'odoo_id'}

    openerp_state_ids = fields.One2many(
        comodel_name='sale.order.state.list',
        inverse_name='prestashop_state_id',
        string='Odoo States',
    )
    odoo_id = fields.Many2one(
        comodel_name='sale.order.state',
        required=True,
        ondelete='cascade',
        string='Sale Order State',
        oldname='openerp_id',
    )


class SaleOrderStateList(models.Model):
    _name = 'sale.order.state.list'

    name = fields.Selection(
        selection=[
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done')
        ],
        string='Odoo State',
        required=True,
    )
    prestashop_state_id = fields.Many2one(
        comodel_name='prestashop.sale.order.state',
        string='PrestaShop State',
    )
    prestashop_id = fields.Integer(
        related='prestashop_state_id.prestashop_id',
        readonly=True,
        store=True,
        string='PrestaShop ID',
    )


@prestashop
class SaleOrderStateAdapter(Component):
    _name = 'prestashop.sale.order.state.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.sale.order.state'

    _prestashop_model = 'order_states'
