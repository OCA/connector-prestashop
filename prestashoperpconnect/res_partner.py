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

from openerp.osv.orm import Model
from openerp.osv import fields
from base_external_referentials.decorator import only_for_referential
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class res_partner(Model):
    _inherit = 'res.partner'

    _columns = {
        'prestashop_email': fields.char('Prestashop Email', size=64,
                                help='This is the customer email in prestashop'),
    }
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

    def _get_last_imported_date(self, cr, uid, external_session, context=None):
        ext_ref_browse = self.pool.get('external.referential').browse(cr,
                                    uid, [external_session.referential_id.id], context=context)[0]
        return ext_ref_browse.last_customer_import_date

    def _set_last_imported_date(self, cr, uid, external_session, date, context=None):
        new_date = date
        if date == 'default':
            new_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        self.pool.get('external.referential').write(cr, uid,[external_session.referential_id.id],
                                                    {'last_customer_import_date': new_date },
                                                    context=context)
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

class res_partner_address(Model):
    _inherit = 'res.partner.address'

    def _get_email(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for address in self.browse(cr, uid, ids, context=context):
            if address.use_prestashop_email:
                res[address.id] = address.partner_id.prestashop_email
            else:
                res[address.id] = address.custom_email
        return res

    def _set_email(self, cr, uid, id, name, value, arg, context=None):
        return cr.execute(
            """
            UPDATE res_partner_address
                SET custom_email = %s
                WHERE id = %s
            """, (value, id))

    _columns = {
        'email': fields.function(_get_email,
                            fnct_inv = _set_email,
                            string='Email',
                            type='char',
                            help='E-Mail'),
        'custom_email': fields.char('Custom Email', size=64),
        'use_prestashop_email': fields.boolean('Use Prestashop Email',
            help="If checked, OpenERP will use the PrestaShop email of the partner form."),

    }

    _defaults = {
        'use_prestashop_email': True,
    }


    def _get_last_imported_date(self, cr, uid, external_session, context=None):
        ext_ref_browse = self.pool.get('external.referential').browse(cr,
                                    uid, [external_session.referential_id.id], context=context)[0]
        return ext_ref_browse.last_customer_address_import_date

    def _set_last_imported_date(self, cr, uid, external_session, date, context=None):
        new_date = date
        if date == 'default':
            new_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        self.pool.get('external.referential').write(cr, uid,[external_session.referential_id.id],
                                                    {'last_customer_address_import_date': new_date },
                                                    context=context)
        return True


