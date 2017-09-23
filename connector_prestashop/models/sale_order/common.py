# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.addons.decimal_precision as dp

from odoo import models, fields, api

from ...components.backend_adapter import GenericAdapter
from ...backend import prestashop

import logging
_logger = logging.getLogger(__name__)


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
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_amount_tax = fields.Float(
        string='Total tax in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_shipping_tax_included = fields.Float(
        string='Total shipping in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_shipping_tax_excluded = fields.Float(
        string='Total shipping in PrestaShop',
        digits=dp.get_precision('Account'),
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


@prestashop
class SaleOrderAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def update_sale_state(self, prestashop_id, datas):
        return self.client.add('order_histories', datas)


@prestashop
class SaleOrderLineAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.line'
    _prestashop_model = 'order_details'


@prestashop
class OrderPaymentAdapter(GenericAdapter):
    _model_name = '__not_exist_prestashop.payment'
    _prestashop_model = 'order_payments'


@prestashop
class OrderDiscountAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.line.discount'
    _prestashop_model = 'order_discounts'
