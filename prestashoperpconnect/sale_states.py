# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Authors :                                                                 #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Mathieu VATEL <mathieu@julius.fr>                                 #
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
from prestashop_osv import prestashop_osv
from base_external_referentials.decorator import only_for_referential
import time

class sale_order_state(osv.osv):
    _name='sale.order.state'
    _description = 'Sale External State'

    _columns = {
        'name': fields.char('Name', size=64, translate=True),
        'template': fields.char('Template', size=64, translate=True),                
    }

sale_order_state()
    
class sale_order_history(osv.osv):
    _name='sale.order.history'
    _description = 'Sale External History'
    
    _order = 'date_add desc'
    
    _columns = {
        'order_id': fields.many2one('sale.order', 'Sale order', required=True, ondelete='cascade'),
        'state_id': fields.many2one('sale.order.state', 'State', required=True),
        'date_add': fields.datetime('Date add'),
    }
    
    _defaults = {
        'date_add': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
sale_order_history()
    
class external_referential(osv.osv):
    _inherit = "external.referential"
    
    def sync_order_state(self, cr, uid, ids, context=None):
        self.import_resources(cr, uid, ids, 'sale.order.state', context=context)
        return True

external_referential()

class sale_order(osv.osv):
    _inherit='sale.order'
    
    _columns = {
        'history_ids': fields.one2many('sale.order.history', 'order_id', 'Prestashop Histories'),
        'external_state_id': fields.related('history_ids', 'state_id', type='many2one', relation='sale.order.state', string='External State'),
    }
sale_order()

class order_state(prestashop_osv):
    _inherit='sale.order.state'
    
class order_history(prestashop_osv):
    _inherit='sale.order.history'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: