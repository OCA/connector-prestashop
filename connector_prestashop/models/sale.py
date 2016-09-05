# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.addons.decimal_precision as dp

from openerp import models, fields, api


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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopSaleOrder(models.Model):
    _name = 'prestashop.sale.order'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_order_line_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line',
        inverse_name='prestashop_order_id',
        string='PrestaShop Order Lines',
    )
    prestashop_discount_line_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line.discount',
        inverse_name='prestashop_order_id',
        string='PrestaShop Discount Lines',
    )
    prestashop_invoice_number = fields.Char('PrestaShop Invoice Number')
    prestashop_delivery_number = fields.Char('PrestaShop Delivery Number')
    total_amount = fields.Float(
        string='Total amount in PrestaShop',
        digits_compute=dp.get_precision('Account'),
        readonly=True,
    )
    total_amount_tax = fields.Float(
        string='Total tax in PrestaShop',
        digits_compute=dp.get_precision('Account'),
        readonly=True,
    )
    total_shipping_tax_included = fields.Float(
        string='Total shipping in PrestaShop',
        digits_compute=dp.get_precision('Account'),
        readonly=True,
    )
    total_shipping_tax_excluded = fields.Float(
        string='Total shipping in PrestaShop',
        digits_compute=dp.get_precision('Account'),
        readonly=True,
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    prestashop_discount_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line.discount',
        inverse_name='odoo_id',
        string='PrestaShop Discount Bindings',
    )


class PrestashopSaleOrderLine(models.Model):
    _name = 'prestashop.sale.order.line'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order.line': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order line',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_order_id = fields.Many2one(
        comodel_name='prestashop.sale.order',
        string='PrestaShop Sale Order',
        required=True,
        ondelete='cascade',
        index=True,
    )

    @api.model
    def create(self, vals):
        ps_sale_order = self.env['prestashop.sale.order'].search([
            ('id', '=', vals['prestashop_order_id'])
        ], limit=1)
        vals['order_id'] = ps_sale_order.odoo_id.id
        return super(PrestashopSaleOrderLine, self).create(vals)


class PrestashopSaleOrderLineDiscount(models.Model):
    _name = 'prestashop.sale.order.line.discount'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order.line': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order line',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_order_id = fields.Many2one(
        comodel_name='prestashop.sale.order',
        string='PrestaShop Sale Order',
        required=True,
        ondelete='cascade',
        index=True,
    )

    @api.model
    def create(self, vals):
        ps_sale_order = self.env['prestashop.sale.order'].search([
            ('id', '=', vals['prestashop_order_id'])
        ], limit=1)
        vals['order_id'] = ps_sale_order.odoo_id.id
        return super(PrestashopSaleOrderLineDiscount, self).create(vals)
