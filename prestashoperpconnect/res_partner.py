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
from datetime import datetime

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

    def _get_filter(self, cr, uid, external_session, step, previous_filter=None, context=None):
        """ see docstring in prestashop_osv """
        last_export = self._get_last_exported_date(cr, uid, external_session, context=context)
        self._set_last_exported_date(cr, uid, external_session, date='default', context=context)
        new_filter = super(res_partner, self)._get_filter(cr, uid, external_session, step,
            previous_filter=previous_filter, context=context)
        new_filter['filter[date_upd]'] = '>['+last_export+']'
        new_filter['date']= '1'

        return new_filter

    def _get_last_exported_date(self, cr, uid, external_session, context=None):
        ext_ref_browse = self.pool.get('external.referential').browse(cr,
                                    uid, [external_session.referential_id.id], context=context)[0]
        return ext_ref_browse.last_customer_import_date

    def _set_last_exported_date(self, cr, uid, external_session, date='default', context=None):
        new_date = date
        if date == 'default':
            new_date = datetime.today().strftime("%Y-%m-%d")
        self.pool.get('external.referential').write(cr, uid,
            [external_session.referential_id.id], {'last_customer_import_date': new_date }, context=context)
        return True

    def run_scheduled_import_customers(self, cr, uid, context=None):
        """
         - search 'external referentials' that must trigger customers import
            (according to prestashop's referential type)
         - trigger import from each referential
        :rtype: boolean
        :return: True when import(s) is ended
        """
        if context is None:
            context = {}
        search_vals = [('code', '=', 'prestashop')]
        type_ext_refs = self.pool.get('external.referential.type').search(cr, uid, search_vals)
        search_vals = [('type_id', 'in', tuple(type_ext_refs))]
        ext_ref_model = self.pool.get('external.referential')
        ext_refs = ext_ref_model.search(cr, uid, search_vals)

        ext_ref_model.import_customers(cr, uid, ext_refs, context=context)

        return True

class external_referential(osv.osv):
    _inherit = 'external.referential'

    _columns = {
        'last_customer_import_date': fields.date('Last cust. imp.', help="Last customer import date"),
    }
