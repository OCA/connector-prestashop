#-*- coding: utf-8 -*-
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
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_write
from openerp.addons.connector.unit.synchronizer import (ExportSynchronizer)
from .unit.backend_adapter import GenericAdapter

from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)
from .connector import get_environment
from backend import prestashop


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
        'name': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'OpenERP State', required=True),
        'prestashop_state_id': fields.many2one(
            'prestashop.sale.order.state',
            'Prestashop State'
        ),
        'prestashop_id': fields.related(
            'prestashop_state_id', 'prestashop_id', string='Prestashop ID',
            type='integer', readonly=True, store=True),
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
        'prestashop_invoice_number': fields.char('PrestaShop Invoice Number',size=64),
        'prestashop_delivery_number': fields.char('PrestaShop Delivery Number',size=64),
    }


@prestashop
class PrestaShopSaleOrderOnChange(SaleOrderOnChange):
    _model_name = 'prestashop.sale.order'


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
            cr,
            uid,
            [prestashop_order_id],
            ['openerp_id'],
            context=context
        )
        order_id = info[0]['openerp_id']
        vals['order_id'] = order_id[0]
        return super(prestashop_sale_order_line, self).create(
            cr,
            uid,
            vals,
            context=context
        )


@prestashop
class SaleOrderStateAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.state'
    _prestashop_model = 'order_states'


@prestashop
class SaleOrderAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def update_sale_state(self, prestashop_id, datas):
        api = self.connect()
        return api.add('order_histories', datas)


@prestashop
class SaleOrderLineAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.line'
    _prestashop_model = 'order_details'


@prestashop
class SaleStateExport(ExportSynchronizer):
    _model_name = ['prestashop.sale.order']

    def run(self, binding_id, state):
        binder = self.get_binder_for_model()
        prestashop_id = binder.to_backend(binding_id)
        datas = {
            'order_history': {
                'id_order': prestashop_id,
                'id_order_state': state,
            }
        }
        self.backend_adapter.update_sale_state(prestashop_id, datas)


# TODO improve me, don't try to export state if the sale order does not come
#      from a prestashop connector
# TODO improve me, make the search on the sale order backend only
@on_record_write(model_names='sale.order')
def prestashop_sale_state_modified(session, model_name, record_id,
                                   fields=None):
    if 'state' in fields:
        sale = session.pool[model_name].browse(
            session.cr,
            session.uid,
            record_id
        )
        state_list_model = 'sale.order.state.list'
        states = session.pool[state_list_model].search(
            session.cr,
            session.uid,
            [('name', '=', sale.state)]
        )

        if states:
            state = session.pool[state_list_model].browse(
                session.cr,
                session.uid,
                states[0]
            )
            export_sale_state.delay(
                session,
                model_name,
                record_id,
                state.prestashop_id,
                priority=20
            )
    return True


@job
def export_sale_state(session, model_name, record_id, new_state):
    inherit_model = 'prestashop.' + model_name
    object_pool = session.pool[inherit_model]
    sale_ids = object_pool.search(session.cr, session.uid, [('openerp_id', '=', record_id)])
    if type(sale_ids) is not list:
        sale_ids = [sale_ids]
    for sale in object_pool.browse(session.cr, session.uid, sale_ids):
        backend_id = sale.backend_id.id
        env = get_environment(session, inherit_model, backend_id)
        sale_exporter = env.get_connector_unit(SaleStateExport)
        return sale_exporter.run(sale.id, new_state)
