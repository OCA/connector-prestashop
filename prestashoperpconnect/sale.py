# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Authors :                                                                 #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Mathieu VATEL <mathieu@julius.fr>                                 #
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

from osv import osv, fields
from base_external_referentials.decorator import only_for_referential, catch_action, commit_now
from base_external_referentials.external_osv import ExternalSession
from datetime import datetime



#TODO improve me, this should be not hardcoded. Need to syncronize prestashop state in OpenERP
PRESTASHOP_MAP_STATE = {
    'progress': 3,
    'manual': 3,
    'done': 5,

}


class sale_order(osv.osv):
    _inherit='sale.order'

    @only_for_referential('prestashop')
    def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, mapping=None, fields=None, context=None):
        result = super(sale_order, self)._get_external_resources(cr, uid, external_session, \
                                            external_id=external_id, resource_filter=resource_filter, \
                                            mapping=mapping, fields=fields, context=context)
        for order in result:
            order_rows_ids = order['order_rows']
            order_rows_details = []
            if not isinstance(order_rows_ids, list):
                order_rows_ids = [order_rows_ids]
            for order_row_id in order_rows_ids:
                order_rows_details.append(self.pool.get('sale.order.line')._get_external_resources(cr, uid, \
                                                                            external_session,
                                                                            order_row_id, context=context)[0])
            order['order_rows'] = order_rows_details
        return result

    @commit_now
    def _get_last_imported_date(self, cr, uid, external_session, context=None):
        sale_shop_browse = self.pool.get('sale.shop').browse(cr,
                                    uid, [external_session.sync_from_object.id], context=context)[0]
        return sale_shop_browse.import_orders_from_date

    @commit_now
    def _set_last_imported_date(self, cr, uid, external_session, date='default', context=None):
        new_date = date
        if date == 'default':
            new_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        self.pool.get('sale.shop').write(cr, uid,
            [external_session.sync_from_object.id], {'import_orders_from_date': new_date }, context=context)
        return True

    def _get_payment_information(self, cr, uid, external_session, order_id, resource, context=None):
        """
        Parse the external resource and return a dict of data converted
        """
        vals = super(sale_order, self)._get_payment_information(cr, uid, external_session, order_id, resource, context=context)
        vals['paid'] = bool(float(resource['total_paid_real']))
        vals['amount'] = float(resource['total_paid_real'])
        return vals

    @catch_action
    def _update_state_in_prestashop(self, cr, uid, sale_id, state, context=None):
        sale = self.browse(cr, uid, sale_id, context=context)
        external_session = ExternalSession(sale.shop_id.referential_id)
        ext_id = self.get_extid(cr, uid, sale_id, external_session.referential_id.id, context=context)
        if PRESTASHOP_MAP_STATE.get(state):
            external_session.connection.add('order_histories', {'order_history':{
                'id_order': ext_id,
                'id_order_state' : PRESTASHOP_MAP_STATE[state]
                }})
        return True

    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order, self).write(cr, uid, ids, vals.copy(), context=context)
        if 'state' in vals:
            for sale in self.browse(cr, uid, ids, context=context):
                if sale.shop_id.type_name and sale.shop_id.type_name.lower() == 'prestashop':
                    self._update_state_in_prestashop(cr, uid, sale.id, vals['state'], context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
