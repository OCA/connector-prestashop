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

from openerp.osv import fields, orm


class sale_order(orm.Model):
    _inherit = 'sale.order'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.res.partner',
            'openerp_id',
            string="PrestaShop Bindings"
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
    }


class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.sale.order.line',
            'openerp_id',
            string="PrestaShop Bindings"
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
    }
