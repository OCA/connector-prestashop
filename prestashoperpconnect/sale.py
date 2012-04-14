# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
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
import netsvc
from prestashop_osv import prestashop_osv
from base_external_referentials.decorator import only_for_referential

class external_shop_group(prestashop_osv):
    _inherit='external.shop.group'

class sale_shop(prestashop_osv):
    _inherit='sale.shop'

class sale_order(prestashop_osv):
    _inherit='sale.order'

    @only_for_referential('prestashop')
    def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, mapping=None, fields=None, context=None):
        result = super(sale_order, self)._get_external_resources(cr, uid, external_session, external_id=external_id, resource_filter=resource_filter, mapping=mapping, fields=fields, context=context)
        order_rows = result[0]['order_rows']
        order_lines = []
        if isinstance(order_rows, dict):
            order_rows = [order_rows]
        for order_row in order_rows:
            order_lines.append(self.pool.get('sale.order.line')._get_external_resources(cr, uid, external_session, order_row['id'], context=context)[0])
        result[0]['order_rows'] = order_lines
        history_ids = []
        if result[0]['id']:
            id_order = int(result[0]['id'])
            if resource_filter is None:
                resource_filter = {}
            resource_filter.update({'filter[id_order]': [id_order]})
            histories = self.pool.get('sale.order.history')._get_external_resource_ids(cr, uid, external_session, resource_filter=resource_filter, context=context)
            for history in histories:
                history_ids.append(self.pool.get('sale.order.history')._get_external_resources(cr, uid, external_session, history, context=context)[0])
            result[0]['history_ids'] = history_ids
        return result

class sale_order_line(prestashop_osv):
    _inherit='sale.order.line'
