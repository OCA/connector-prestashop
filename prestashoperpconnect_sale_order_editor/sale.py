# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   prestashoperpconnect_sale_order_editor for OpenERP                        #
#   Copyright (C) 2012 Akretion Benoît GUILLOT <benoit.guillot@akretion.com>  #
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
from base_external_referentials.external_osv import ExternalSession

class sale_order(osv.osv):

    _inherit = "sale.order"

    def edit_prestashop_order(self, cr, uid, ids, context=None):
        for sale_order in self.browse(cr, uid, ids, context=context):
            external_session = ExternalSession(sale_order.referential_id, sale_order)
            ext_id = sale_order.get_extid(external_session.referential_id.id, context=context)
            prestashop_order = external_session.connection.get('orders', ext_id)
            oe_line_ids = [l.ext_ref_line for l in sale_order.order_line if l.ext_ref_line]
            presta_lines = prestashop_order['order']['associations']['order_rows']['order_row']
            if isinstance(presta_lines, dict): presta_lines = [presta_lines]
            for presta_line in presta_lines:
                if not presta_line['id'] in oe_line_ids:
                    del_line = external_session.connection.delete('order_details', presta_line['id'])
        return True
