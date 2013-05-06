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
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_write
from openerp.addons.connector.unit.synchronizer import (ExportSynchronizer)
from openerp.addons.connector.exception import (MappingError,
                                                InvalidDataError,
                                                IDMissingInBackend)
from .unit.backend_adapter import GenericAdapter

from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)
from .connector import get_environment
from backend import prestashop


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
        'prestashop_order_line_ids': fields.one2many(
            'prestashop.sale.order.line',
            'prestashop_order_id',
            'Prestashop Order Lines'
        ),
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

#
#@prestashop
#class SaleOrderStateAdapter(GenericAdapter):
#    _model_name = 'sale.order'
#    _prestashop_model = 'order_histories'
#
#
#@prestashop
#class SaleStateExport(ExportSynchronizer):
#    _model_name = ['sale.order']
#
#    def run(self, binding_id, state):
#        binder = self.get_binder_for_model()
#        prestashop_id = binder.to_backend(binding_id)
#        data =  {'order_history': {
#                    'id_order': prestashop_id,
#                    'id_order_state': state,
#                    }
#                }
#        #self.backend_adapter.update_inventory(prestashop_id, 'order_histories',data)
#        adapter = SaleOrderStateAdapter()
#        adapter.create(prestashop_id, data)
#
##TODO improve me, this should be not hardcoded. Need to syncronize prestashop state in OpenERP
#PRESTASHOP_MAP_STATE = {
#    'progress': 3,
#    'manual': 3,
#    'done': 5,
#}
#
#@on_record_write(model_names='sale.order')
#def prestashop_sale_state_modified(session, model_name, record_id, fields=None):
#    print fields
#    #import pdb;pdb.set_trace()
#    if 'state' in fields:
#        sale = session.pool[model_name].read(session.cr, session.uid, record_id, ['state'])
#        if sale['state'] in PRESTASHOP_MAP_STATE:
#            export_sale_state(session, model_name, record_id, PRESTASHOP_MAP_STATE[sale['state']])
#        return True
#        import pdb;pdb.set_trace()
#    #    export_product_inventory.delay(session, model_name,
#    #                                   record_id, fields=inventory_fields,
#    #                                   priority=20)
#    return True
#
#@job
#def export_sale_state(session, model_name, record_id, new_state):
#    inherit_model = 'prestashop.' + model_name
#    sale = session.pool[inherit_model].browse(session.cr, session.uid, record_id)
#    import pdb;pdb.set_trace()
#    backend_id = sale.backend_id.id
#    env = get_environment(session, inherit_model, backend_id)
#    sale_exporter = env.get_connector_unit(SaleStateExport)
#    return sale_exporter.run(record_id, new_state)







#
#@prestashop
#class SaleOrderAdapter(GenericAdapter):
#    _model_name = 'prestashop.stock.picking.out'
#    _prestashop_model = 'sales_order_shipment'
#
#    def _call(self, method, arguments):
#        try:
#            return super(StockPickingAdapter, self)._call(method, arguments)
#        except xmlrpclib.Fault as err:
#            # this is the error in the Prestashop API
#            # when the shipment does not exist
#            if err.faultCode == 100:
#                raise IDMissingInBackend
#            else:
#                raise
#
#    def create(self, order_id, items, comment, email, include_comment):
#        """ Create a record on the external system """
#        return self._call('%s.create' % self._prestashop_model,
#                          [order_id, items, comment, email, include_comment])
#
#    def add_tracking_number(self, prestashop_id, carrier_code,
#                            tracking_title, tracking_number):
#        return self._call('%s.addTrack' % self._prestashop_model,
#                          [prestashop_id, carrier_code,
#                           tracking_title, tracking_number])
#
#
#@prestashop
#class PrestashopSaleStateExport(ExportSynchronizer):
#    _model_name = ['prestashop.sale.order']
#
#    def _validate(self, picking):
#        if picking.state != 'done':  # should not happen
#            raise ValueError("Wrong value for picking state, "
#                             "it must be 'done', found: %s" % picking.state)
#        if not picking.carrier_id.prestashop_carrier_code:
#            raise FailedJobError("Wrong value for the Prestashop carrier code "
#                                 "defined in the picking.")
#
#    def run(self, binding_id):
#        """ Export the sale order state to Prestashop """
#        # verify the picking is done + prestashop id exists
#        sale = self.session.browse(self.model._name, binding_id)
#        if sale.state in PRESTASHOP_MAP_STATE:
#        #if PRESTASHOP_MAP_STATE.get(state):
#            external_session.connection.add('order_histories', {'order_history':{
#                'id_order': ext_id,
#                'id_order_state' : PRESTASHOP_MAP_STATE[state]
#                }})
#        #tracking_args = self._get_tracking_args(picking)
#        self.backend_adapter.add_tracking_number(prestashop_picking_id,
#                                                 *tracking_args)
#
#        #carrier = picking.carrier_id
#        #if not carrier:
#        #    return FailedJobError('The carrier is missing on the picking %s.' %
#        #                          picking.name)
#        #
#        #if not carrier.prestashop_export_tracking:
#        #    return _('The carrier %s does not export '
#        #             'tracking numbers.') % carrier.name
#        #if not picking.carrier_tracking_ref:
#        #    return _('No tracking number to send.')
#        #
#        #prestashop_picking_id = picking.prestashop_id
#        #if prestashop_picking_id is None:
#        #    raise NoExternalId("No value found for the picking ID on "
#        #                       "Prestashop side, the job will be retried later.")
#        #
#        #self._validate(picking)
#        #self._check_allowed_carrier(picking, prestashop_picking_id)
