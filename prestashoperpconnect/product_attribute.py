# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 20121 Akretion Benoît GUILLOT <benoit.guillot@akretion.com> #
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

class product_attribute(prestashop_osv):
    _inherit = 'product.attribute'

    _columns = {
        'presta_position': fields.integer('Prestashop Position'),
    }

    def _get_last_exported_date(self, cr, uid, external_session, context=None):
        return external_session.referential_id.last_product_attributes_export_date

    def _set_last_exported_date(self, cr, uid, external_session, date, context=None):
        return external_session.referential_id.write({'last_product_attributes_export_date': date})

    @only_for_referential('prestashop')
    def _transform_and_send_one_resource(self, cr, uid, external_session, resource, resource_id,
                            update_date, mapping, mapping_id, defaults=None, context=None):
        option_ids = resource['no_lang']['option_ids']
        res = super(product_attribute, self)._transform_and_send_one_resource(cr, uid, external_session, 
resource, resource_id, update_date, mapping, mapping_id, defaults=defaults, context=context)
        for option_id in option_ids:
            self.pool.get('attribute.option')._export_one_resource(cr, uid, external_session, option_id, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
