# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Benoît GUILLOT <benoit.guillot@akretion.com>                      #
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

from openerp.osv import fields, orm
from openerp.addons.connector.decorator import only_for_referential


class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.res.partner', 'openerp_id',
            string="PrestaShop Bindings"),
        'birthday': fields.date('Birthday'),
        'prestashop_address_bind_ids': fields.one2many(
            'prestashop.address', 'openerp_id',
            string="PrestaShop Address Bindings"),
        'company': fields.char('Company'),
    }


class prestashop_res_partner(orm.Model):
    _name = 'prestashop.res.partner'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    _rec_name = 'shop_group_id'

    def _get_prest_partner_from_website(self, cr, uid, ids, context=None):
        prest_partner_obj = self.pool['prestashop.res.partner']
        return prest_partner_obj.search(cr, uid,
                                [('shop_group_id', 'in', ids)],
                                context=context)

    _columns = {
        'openerp_id': fields.many2one('res.partner',
                                      string='Partner',
                                      required=True,
                                      ondelete='cascade'),
        'backend_id': fields.related('shop_group_id', 'backend_id',
                                     type='many2one',
                                     relation='prestashop.backend',
                                     string='Prestashop Backend',
                                     store={
                                        'prestashop.res.partner':
                                        (lambda self, cr, uid, ids, c=None: ids,
                                         ['shop_group_id'],
                                         10),
                                        'prestashop.website':
                                        (_get_prest_partner_from_website,
                                         ['backend_id'],
                                         20),
                                        },
                                     readonly=True),
        'shop_group_id': fields.many2one('prestashop.shop.group',
                                      string='PrestaShop Shop Group',
                                      required=True,
                                      ondelete='restrict'),
        'group_id': fields.many2one('prestashop.res.partner.category',
                                    string='PrestaShop Group (Category)'),
        'date_add': fields.datetime('Created At (on PrestaShop)',
                                      readonly=True),
        'date_upd': fields.datetime('Updated At (on PrestaShop)',
                                      readonly=True),
        'emailid': fields.char('E-mail address'),
        'newsletter': fields.boolean('Newsletter'),
        'prestashop_default_category': fields.many2one('res.partner.category',
            'PrestaShop default category',
            help="This field is synchronized with the field "
            "'Default customer group' in PrestaShop."),
    }

    _sql_constraints = [
        ('prestashop_uniq', 'unique(shop_group_id, prestashop_id)',
         'A partner with the same ID on PrestaShop already exists for this website.'),
    ]


class prestashop_address(orm.Model):
    _name = 'prestashop.address'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    _rec_name = 'backend_id'

    def _get_prest_address_from_partner(self, cr, uid, ids, context=None):
        prest_address_obj = self.pool['prestashop.address']
        return prest_address_obj.search(cr, uid,
                                [('prestashop_partner_id', 'in', ids)],
                                context=context)

    _columns = {
        'openerp_id': fields.many2one('res.partner',
                                      string='Partner',
                                      required=True,
                                      ondelete='cascade'),
        'date_add': fields.datetime('Created At (on Prestashop)',
                                      readonly=True),
        'date_upd': fields.datetime('Updated At (on Prestashop)',
                                      readonly=True),
        'prestashop_partner_id': fields.many2one('prestashop.res.partner',
                                              string='Prestashop Partner',
                                              required=True,
                                              ondelete='cascade'),
        'backend_id': fields.related('prestashop_partner_id', 'backend_id',
                                     type='many2one',
                                     relation='prestashop.backend',
                                     string='Prestashop Backend',
                                     store={
                                        'prestashop.address':
                                        (lambda self, cr, uid, ids, c=None: ids,
                                         ['prestashop_partner_id'],
                                         10),
                                        'prestashop.res.partner':
                                        (_get_prest_address_from_partner,
                                         ['backend_id', 'shop_group_id'],
                                         20),
                                        },
                                     readonly=True),
        'shop_group_id': fields.related('prestashop_partner_id', 'shop_group_id',
                                     type='many2one',
                                     relation='prestashop.shop.group',
                                     string='PrestaShop Shop Group',
                                     store={
                                        'prestashop.address':
                                        (lambda self, cr, uid, ids, c=None: ids,
                                         ['prestashop_partner_id'],
                                         10),
                                        'prestashop.res.partner':
                                        (_get_prest_address_from_partner,
                                         ['shop_group_id'],
                                         20),
                                        },
                                     readonly=True),
        'vat_number': fields.char('PrestaShop VAT'),
    }

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A partner address with the same ID on PrestaShop already exists.'),
    ]


class res_partner_category(orm.Model):
    _inherit = 'res.partner.category'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.res.partner.category',
            'openerp_id',
            string='PrestaShop Bindings',
            readonly=True),
    }


class prestashop_res_partner_category(orm.Model):
    _name = 'prestashop.res.partner.category'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner.category': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one('res.partner.category',
                                       string='Partner Category',
                                       required=True,
                                       ondelete='cascade'),
        'date_add': fields.datetime('Created At (on Prestashop)',
                                      readonly=True),
        'date_upd': fields.datetime('Updated At (on Prestashop)',
                                      readonly=True),
        # TODO add prestashop shop when the field will be available in the api.
        # we have reported the bug for it
        # see http://forge.prestashop.com/browse/PSCFV-8284
    }

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A partner group with the same ID on PrestaShop already exists.'),
    ]






#Below : from version 6.1 !!!

class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        #'prestashop_email': fields.char('PrestaShop E-mail', size=64,
        #    help='This is the customer e-mail in PrestaShop'),
        #'prestashop_default_category': fields.many2one('res.partner.category',
        #    'PrestaShop default category',
        #    help="This field is synchronized with the field 'Default customer group' in PrestaShop."),
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

    #def _get_last_imported_date(self, cr, uid, external_session, context=None):
    #    ext_ref_browse = self.pool.get('external.referential').browse(cr,
    #                                uid, [external_session.referential_id.id], context=context)[0]
    #    return ext_ref_browse.last_customer_import_date
    #
    #def _set_last_imported_date(self, cr, uid, external_session, date, context=None):
    #    new_date = date
    #    if date == 'default':
    #        new_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    #    self.pool.get('external.referential').write(cr, uid,[external_session.referential_id.id],
    #                                                {'last_customer_import_date': new_date },
    #                                                context=context)
    #    return True

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

#class res_partner_address(Model):
#    _inherit = 'res.partner.address'

    #def _auto_init(self, cr, context=None):
    #    # email field will be replace by a function field
    #    # in order to not loss all customer email
    #    # we move them in custom email
    #    # Also for existing record we use custom email
    #    first_install=False
    #    cr.execute("SELECT column_name FROM information_schema.columns "
    #               "WHERE table_name = 'res_partner_address' "
    #               "AND column_name = 'custom_email'")
    #    if not cr.fetchone():
    #        first_install = True
    #        cr.execute("ALTER TABLE res_partner_address "
    #                   "RENAME COLUMN email TO custom_email")
    #    res = super(res_partner_address, self)._auto_init(cr, context=context)
    #    if first_install:
    #        cr.execute("UPDATE res_partner_address SET use_prestashop_email=False")
    #    return res

    #def _get_email(self, cr, uid, ids, field_name, args, context=None):
    #    res = {}
    #    for address in self.browse(cr, uid, ids, context=context):
    #        if address.use_prestashop_email:
    #            res[address.id] = address.partner_id.prestashop_email
    #        else:
    #            res[address.id] = address.custom_email
    #    return res
    #
    #def _set_email(self, cr, uid, id, name, value, arg, context=None):
    #    self.write(cr, uid, id, {'custom_email': value}, context=context)
    #    return True
    #
    #def _get_partner_addr_from_partner(self, cr, uid, ids, context=None):
    #    return self.pool.get('res.partner.address').search(cr, uid, [('partner_id', 'in', ids)], context=context)

    #_columns = {
    #    'email': fields.function(_get_email, fnct_inv=_set_email,
    #        string='E-Mail', type='char', size=240, store={
    #            'res.partner.address': (lambda self, cr, uid, ids, c={}: ids, ['custom_email', 'use_prestashop_email', 'partner_id'], 10),
    #            'res.partner': (_get_partner_addr_from_partner, ['prestashop_email'], 20),
    #        }),
    #    'custom_email': fields.char('Custom E-mail', size=240),
    #    'use_prestashop_email': fields.boolean('Use PrestaShop Email',
    #        help="If checked, OpenERP will use the PrestaShop email of the partner form."),
    #
    #}

    #_defaults = {
    #    'use_prestashop_email': True,
    #}


    #def _get_last_imported_date(self, cr, uid, external_session, context=None):
    #    ext_ref_browse = self.pool.get('external.referential').browse(cr,
    #                                uid, [external_session.referential_id.id], context=context)[0]
    #    return ext_ref_browse.last_customer_address_import_date
    #
    #def _set_last_imported_date(self, cr, uid, external_session, date, context=None):
    #    new_date = date
    #    if date == 'default':
    #        new_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    #    self.pool.get('external.referential').write(cr, uid,
    #        [external_session.referential_id.id],
    #        {'last_customer_address_import_date': new_date}, context=context)
    #    return True
