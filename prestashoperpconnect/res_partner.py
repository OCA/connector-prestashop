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
        'prestashop_email': fields.char('PrestaShop E-mail', size=64,
                                help='This is the customer e-mail in PrestaShop'),
        'prestashop_default_category': fields.many2one('res.partner.category', 'PrestaShop default category', help="This field is synchronized with the field 'Default customer group' in PrestaShop."),
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

    def _auto_init(self, cr, context=None):
        # email field will be replace by a function field
        # in order to not loss all customer email
        # we move them in custom email
        # Also for existing record we use custom email
        first_install=False
        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_partner_address' "
                   "AND column_name = 'custom_email'")
        if not cr.fetchone():
            first_install = True
            cr.execute("ALTER TABLE res_partner_address "
                       "RENAME COLUMN email TO custom_email")
        res = super(res_partner_address, self)._auto_init(cr, context=context)
        if first_install:
            cr.execute("UPDATE res_partner_address SET use_prestashop_email=False")
        return res

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

    def _get_partner_addr_from_partner(self, cr, uid, ids, context=None):
        return self.pool.get('res.partner.address').search(cr, uid, [('partner_id', 'in', ids)], context=context)

    _columns = {
        'email': fields.function(_get_email, fnct_inv=_set_email,
            string='E-Mail', type='char', size=240, store={
                'res.partner.address': (lambda self, cr, uid, ids, c={}: ids, ['custom_email', 'use_prestashop_email', 'partner_id'], 10),
                'res.partner': (_get_partner_addr_from_partner, ['prestashop_email'], 20),
            }),
        'custom_email': fields.char('Custom E-mail', size=240),
        'use_prestashop_email': fields.boolean('Use PrestaShop Email',
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
        self.pool.get('external.referential').write(cr, uid,
            [external_session.referential_id.id],
            {'last_customer_address_import_date': new_date}, context=context)
        return True


