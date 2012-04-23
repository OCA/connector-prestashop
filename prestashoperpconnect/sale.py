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
from prestashop_osv import prestashop_osv
from base_external_referentials.decorator import only_for_referential
import time

class external_shop_group(prestashop_osv):
    _inherit='external.shop.group'

class sale_order(prestashop_osv):
    _inherit='sale.order'

    @only_for_referential('prestashop')
    def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, mapping=None, fields=None, context=None):
        result = super(sale_order, self)._get_external_resources(cr, uid, external_session, \
                                            external_id=external_id, resource_filter=resource_filter, \
                                            mapping=mapping, fields=fields, context=context)
        order_rows = result[0]['order_rows']
        order_lines = []
        if not isinstance(order_rows, list):
            order_rows = [order_rows]
        for order_row in order_rows:
            if order_row.get('id'):
                order_lines.append(self.pool.get('sale.order.line')._get_external_resources(cr, uid, \
                                                                        external_session, order_row['id'], context=context)[0])
        result[0]['order_rows'] = order_lines
        history_ids = []
        if result[0]['id']:
            id_order = int(result[0]['id'])
            if resource_filter is None:
                resource_filter = {}
            resource_filter.update({'filter[id_order]': [id_order]})
            histories = self.pool.get('sale.order.history')._get_external_resource_ids(cr, uid, external_session,\
                                                                    resource_filter=resource_filter, context=context)
            for history in histories:
                history_ids.append(self.pool.get('sale.order.history')._get_external_resources(cr, uid, \
                                                                            external_session, history, context=context)[0])
            result[0]['history_ids'] = history_ids
        return result

class sale_order_line(prestashop_osv):
    _inherit='sale.order.line'
    
class sale_shop(prestashop_osv):
    _inherit = 'sale.shop'

    def get_shop_lang_to_export(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        lang_code = []
        shop_data = self.browse(cr, uid, ids)
        for shop in shop_data:
            lang_code = [x.code for x in shop.exportable_lang_ids]
        return lang_code

    def export_prestashop_catalog(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        context['lang_to_export'] = self.get_shop_lang_to_export(cr, uid, ids, context=context)
        self.export_resources(cr, uid, ids, 'product.category', context=context)
        self.export_resources(cr, uid, ids, 'product.template', context=context)
        #TODO update the last date
        #I don't know where it's thebest to update it ere or in the epxot functions
        #take care about concurent write with diferent cursor
        return True
    
#    @only_for_referential('prestashop')
#    def update_orders(self, cr, uid, ids, context=None):
#        if context is None:
#            context = {}
#        for shop in self.browse(cr, uid, ids):
#            #get all orders, which the state is not draft and the date of modification is superior to the last update, to exports 
#            req = "select ir_model_data.res_id, ir_model_data.name from sale_order inner join ir_model_data on sale_order.id = ir_model_data.res_id where ir_model_data.model='sale.order' and sale_order.shop_id=%s and ir_model_data.referential_id IS NOT NULL "
#            param = (shop.id,)
#
#            if shop.last_update_order_export_date:
#                req += "and sale_order.write_date > %s" 
#                param = (shop.id, shop.last_update_order_export_date)
#
#            cr.execute(req, param)
#            results = cr.fetchall()
#
#            for result in results:
#                ids = self.pool.get('sale.order').search(cr, uid, [('id', '=', result[0])])
#                if ids:
#                    id = ids[0]
#                    order = self.pool.get('sale.order').browse(cr, uid, id, context)
#                    order_ext_id = result[1].split('sale_order/')[1]
#                    self.update_shop_orders(cr, uid, order, order_ext_id, context)
#                    logging.getLogger('external_synchro').info("Successfully updated order with OpenERP id %s and ext id %s in external sale system" % (id, order_ext_id))
#            self.pool.get('sale.shop').write(cr, uid, shop.id, {'last_update_order_export_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
#        return False
    
#    @only_for_referential('prestashop')
#    def update_shop_orders(self, cr, uid, order, ext_id, context=None):
#        if context is None: context = {}
#        result = {}
#        date = '2012-04-15 10:46:57'
#        history_obj = self.pool.get('sale.order.history')
#        history_ids = history_obj.search(cr, uid, [('order_id', '=', order.id),('date_add', '>=', date)])
#        if history_ids:
#            self.export_history(cr, uid, [2], history_ids, context=context)
#        return result
#    
#    def export_history(self, cr, uid, ids, history_ids, context=None):
#        self.export_resources(cr, uid, ids, history_ids, 'sale.order.history', context=context)
#        return True

class sale_shop_osv(osv.osv):
    _inherit = 'sale.shop'
    
    _columns = {
        'exportable_lang_ids': fields.many2many('res.lang', 'shop_lang_rel', 'lang_id', 'shop_id', 'Exportable Languages'),
    }
    
sale_shop_osv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
