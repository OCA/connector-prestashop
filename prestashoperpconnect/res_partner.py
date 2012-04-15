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
from prestashop_osv import prestashop_osv
from base_external_referentials.decorator import only_for_referential

class res_partner(prestashop_osv):
    _inherit='res.partner'
    
    @only_for_referential('prestashop')
    def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, mapping=None, fields=None, context=None):
        result = super(res_partner, self)._get_external_resources(cr, uid, external_session, external_id=external_id, resource_filter=resource_filter, mapping=mapping, fields=fields, context=context)
        main_contact = {'contact_type': 'default'}
        if result and result[0]:
            email = result[0].get('email', False) or ''
            if email:
                main_contact.update({'email': email})
            name = result[0].get('firstname', False) or ''
            name += (result[0].get('lastname', False) and ' ' + result[0].get('lastname', False)) or ''
            if name:
                main_contact.update({'contact_name': name})
            result[0]['main_contact'] = [main_contact]
        return result