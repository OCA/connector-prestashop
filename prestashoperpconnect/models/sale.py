# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2013 Akretion                                               #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

import openerp.addons.decimal_precision as dp

from openerp.osv import fields, orm


class sale_order_state(orm.Model):
    _name = 'sale.order.state'

    _columns = {
        'name': fields.char('Name', size=128, translate=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'prestashop_bind_ids': fields.one2many(
            'prestashop.sale.order.state',
            'openerp_id',
            string="Prestashop Bindings"
        ),
    }


class prestashop_sale_order_state(orm.Model):
    _name = 'prestashop.sale.order.state'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order.state': 'openerp_id'}

    _columns = {
        'openerp_state_ids': fields.one2many(
            'sale.order.state.list',
            'prestashop_state_id',
            'OpenERP States'
        ),
        'openerp_id': fields.many2one(
            'sale.order.state',
            string='Sale Order State',
            required=True,
            ondelete='cascade'
        ),
    }


class sale_order_state_list(orm.Model):
    _name = 'sale.order.state.list'

    _columns = {
        'name': fields.selection(
            [
                ('draft', 'Draft Quotation'),
                ('sent', 'Quotation Sent'),
                ('cancel', 'Cancelled'),
                ('waiting_date', 'Waiting Schedule'),
                ('progress', 'Sales Order'),
                ('manual', 'Sale to Invoice'),
                ('invoice_except', 'Invoice Exception'),
                ('done', 'Done'),
            ],
            'OpenERP State',
            required=True
        ),
        'prestashop_state_id': fields.many2one(
            'prestashop.sale.order.state',
            'Prestashop State'
        ),
        'prestashop_id': fields.related(
            'prestashop_state_id',
            'prestashop_id',
            string='Prestashop ID',
            type='integer',
            readonly=True,
            store=True
        ),
    }


class sale_order(orm.Model):
    _inherit = 'sale.order'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.sale.order',
            'openerp_id',
            string="Prestashop Bindings"
        ),
    }


class prestashop_sale_order(orm.Model):
    _name = 'prestashop.sale.order'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'sale.order',
            string='Sale Order',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_order_line_ids': fields.one2many(
            'prestashop.sale.order.line',
            'prestashop_order_id',
            'Prestashop Order Lines'
        ),
        'prestashop_discount_line_ids': fields.one2many(
            'prestashop.sale.order.line.discount',
            'prestashop_order_id',
            'Prestashop Discount Lines'
        ),
        'prestashop_invoice_number': fields.char(
            'PrestaShop Invoice Number', size=64
        ),
        'prestashop_delivery_number': fields.char(
            'PrestaShop Delivery Number', size=64
        ),
        'total_amount': fields.float(
            'Total amount in Prestashop',
            digits_compute=dp.get_precision('Account'),
            readonly=True
        ),
        'total_amount_tax': fields.float(
            'Total tax in Prestashop',
            digits_compute=dp.get_precision('Account'),
            readonly=True
        ),
        'total_shipping_tax_included': fields.float(
            'Total shipping in Prestashop',
            digits_compute=dp.get_precision('Account'),
            readonly=True
        ),
        'total_shipping_tax_excluded': fields.float(
            'Total shipping in Prestashop',
            digits_compute=dp.get_precision('Account'),
            readonly=True
        ),
    }


class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.sale.order.line',
            'openerp_id',
            string="PrestaShop Bindings"
        ),
        'prestashop_discount_bind_ids': fields.one2many(
            'prestashop.sale.order.line.discount',
            'openerp_id',
            string="PrestaShop Discount Bindings"
        ),
    }


class prestashop_sale_order_line(orm.Model):
    _name = 'prestashop.sale.order.line'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order.line': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'sale.order.line',
            string='Sale Order line',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_order_id': fields.many2one(
            'prestashop.sale.order',
            'Prestashop Sale Order',
            required=True,
            ondelete='cascade',
            select=True
        ),
    }

    def create(self, cr, uid, vals, context=None):
        prestashop_order_id = vals['prestashop_order_id']
        info = self.pool['prestashop.sale.order'].read(
            cr, uid,
            [prestashop_order_id],
            ['openerp_id'],
            context=context
        )
        order_id = info[0]['openerp_id']
        vals['order_id'] = order_id[0]
        return super(prestashop_sale_order_line, self).create(
            cr, uid, vals, context=context
        )


class prestashop_sale_order_line_discount(orm.Model):
    _name = 'prestashop.sale.order.line.discount'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order.line': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'sale.order.line',
            string='Sale Order line',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_order_id': fields.many2one(
            'prestashop.sale.order',
            'Prestashop Sale Order',
            required=True,
            ondelete='cascade',
            select=True
        ),
    }
