# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Alexis de Lattre <alexis.delattre@akretion.com>                   #
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

from osv import osv, fields
from tools.translate import _
from base_external_referentials.decorator import only_for_referential
from base_external_referentials.external_osv import ExternalSession
from prestapyt import PrestaShopWebServiceError, PrestaShopAuthenticationError, PrestaShopWebService, PrestaShopWebServiceDict
from openerp.tools.config import config

from base_external_referentials.external_referentials import REF_VISIBLE_FIELDS
REF_VISIBLE_FIELDS['Prestashop'] = ['location', 'apipass']


class external_referential(osv.osv):
    _inherit = "external.referential"

    _columns = {
        'last_customer_import_date': fields.datetime('Last Cust Imp', help="Last customer import date"),
        'last_customer_address_import_date': fields.datetime('Last Address Imp',
                                                        help="Last customer address import date"),
        'last_product_attributes_export_date' : fields.datetime('Last Product Attributes Export Time'),
        'active_language_ids': fields.many2many('res.lang', 'active_presta_lang', 'referential_id', 'lang_id', 'Active Languages'),
    }

    _lang_support = 'fields_with_no_lang'

    @only_for_referential('prestashop')
    def external_connection(self, cr, uid, id, debug=False, logger=False, context=None):
        if isinstance(id, list):
            id = id[0]
        referential = self.browse(cr, uid, id, context=context)
        prestashop = PrestaShopWebServiceDict('%s/api'%referential.location, referential.apipass, debug=referential.debug)
        try:
            prestashop.head('')
        except PrestaShopAuthenticationError, e:
            if config['debug_mode']: raise
            raise osv.except_osv(_("Connection Error"), _("Could not connect to the PrestaShop webservice\nCheck the webservice URL and password\nHTTP error code: %s"%e.error_code))
        return prestashop

    def _compare_languages(self, cr, uid, ps_field, oe_field, ps_dict, oe_dict, context=None):
        if len(oe_dict[oe_field]) >= 2 \
            and len(ps_dict[0][ps_field]) >=2 \
            and oe_dict[oe_field][0:2].lower() == ps_dict[0][ps_field][0:2].lower():
            return True
        else:
            return False

    def _compare_countries(self, cr, uid, ps_field, oe_field, ps_dict, oe_dict, context=None):
        if len(oe_dict[oe_field]) >= 2 \
            and len(ps_dict[0][ps_field]) >=2 \
            and oe_dict[oe_field][0:2].lower() == ps_dict[0][ps_field][0:2].lower():
            return True
        else:
            return False

    def _compare_currencies(self, cr, uid, ps_field, oe_field, ps_dict, oe_dict, context=None):
        if len(oe_dict[oe_field]) == 3 \
            and len(ps_dict[0][ps_field]) == 3 \
            and oe_dict[oe_field][0:3].lower() == ps_dict[0][ps_field][0:3].lower():
            return True
        else:
            return False

    def _compare_taxes(self, cr, uid, ps_field, oe_field, ps_dict, oe_dict, context=None):
        if oe_dict['type_tax_use'] == 'sale'\
                    and abs(oe_dict[oe_field]*100 - float(ps_dict[0][ps_field]))<0.01:
            return True
        else:
            return False

    def _bidirectional_synchro(self, cr, uid, external_session, obj_readable_name, oe_obj, ps_field, ps_readable_field, oe_field, oe_readable_field, compare_function, context=None):
        external_session.logger.info(_("[%s] Starting synchro between OERP and PS") %obj_readable_name)
        referential_id = external_session.referential_id.id
        nr_ps_already_mapped = 0
        nr_ps_mapped = 0
        nr_ps_not_mapped = 0
        # Get all OERP obj
        oe_ids = oe_obj.search(cr, uid, [], context=context)
        fields_to_read = [oe_field]
        if not oe_readable_field == oe_field:
            fields_to_read.append(oe_readable_field)
        oe_list_dict = oe_obj.read(cr, uid, oe_ids, fields_to_read, context=context)
        #print "oe_list_dict=", oe_list_dict
        # Get the IDS from PS
        ps_ids = oe_obj._get_external_resource_ids(cr, uid, external_session, context=context)
        #print "ps_ids=", ps_ids
        if not ps_ids:
            raise osv.except_osv(_('Error :'), _('Failed to query %s via PS webservice')% obj_readable_name)
        # Loop on all PS IDs
        for ps_id in ps_ids:
            # Check if the PS ID is already mapped to an OE ID
            oe_id = oe_obj.extid_to_existing_oeid(cr, uid, external_id=ps_id, referential_id=referential_id, context=context)
            #print "oe_c_id=", oe_id
            if oe_id:
                # Do nothing for the PS IDs that are already mapped
                external_session.logger.debug(_("[%s] PS ID %s is already mapped to OERP ID %s") %(obj_readable_name, ps_id, oe_id))
                nr_ps_already_mapped += 1
            else:
                # PS IDs not mapped => I try to match between the PS ID and the OE ID
                # I read field in PS
                ps_dict = oe_obj._get_external_resources(cr, uid, external_session, ps_id, context=context)
                #print "ps_dict=", ps_dict
                mapping_found = False
                # Loop on OE IDs
                for oe_dict in oe_list_dict:
                    # Search for a match
                    if compare_function(cr, uid, ps_field, oe_field, ps_dict, oe_dict, context=context):
                        # it matches, so I write the external ID
                        oe_obj.create_external_id_vals(cr, uid, existing_rec_id=oe_dict['id'], external_id=ps_id, referential_id=referential_id, context=context)
                        external_session.logger.info(
                            _("[%s] Mapping PS '%s' (%s) to OERP '%s' (%s)")
                            % (obj_readable_name, ps_dict[0][ps_readable_field], ps_dict[0][ps_field], oe_dict[oe_readable_field], oe_dict[oe_field]))
                        nr_ps_mapped += 1
                        mapping_found = True
                        break
                if not mapping_found:
                    # if it doesn't match, I just print a warning
                    external_session.logger.warning(
                        _("[%s] PS '%s' (%s) was not mapped to any OERP entry")
                        % (obj_readable_name, ps_dict[0][ps_readable_field], ps_dict[0][ps_field]))
                    nr_ps_not_mapped += 1
        external_session.logger.info(
            _("[%s] Synchro between OERP and PS successfull") %obj_readable_name)
        external_session.logger.info(_("[%s] Number of PS entries already mapped = %s")
            % (obj_readable_name, nr_ps_already_mapped))
        external_session.logger.info(_("[%s] Number of PS entries mapped = %s")
            % (obj_readable_name, nr_ps_mapped))
        external_session.logger.info(_("[%s] Number of PS entries not mapped = %s")
            % (obj_readable_name, nr_ps_not_mapped))
        return True


    @only_for_referential('prestashop')
    def _import_resources(self, cr, uid, external_session, defaults=None, context=None, method="search_then_read"):
        referential_id = external_session.referential_id.id
        """TODO Make this more clean because I think this "version" field is not the best way to handle this
        (The 1.4.3 version of Prestashop doesn't have external shop groups)
        """
        if external_session.referential_id.version_id.code >= 'prestashop1500' or not external_session.referential_id.version_id.code:
            self.import_resources(cr, uid, [referential_id], 'external.shop.group', context=context)
        else:
            ext_shop_group_obj = self.pool.get('external.shop.group')
            group_id = False
            group_ids = ext_shop_group_obj.search(cr, uid, [('referential_id', '=', referential_id)])
            if not group_ids:
                group_shop_vals = {'name': "Shop group" + external_session.referential_id.name, 'referential_id': referential_id}
                group_id = ext_shop_group_obj.create(cr, uid, group_shop_vals)
            else:
                group_id = group_ids[0]
            if context == None:
                context = {}
            if group_id:
                context.update({'default_shop_group_id':group_id})
        self.import_resources(cr, uid, [referential_id], 'sale.shop', context=context)
        return {}


    @only_for_referential('prestashop')
    def import_base_objects(self, cr, uid, ids, context=None):
        cur_referential = self.browse(cr, uid, ids[0], context=context)
        external_session = ExternalSession(cur_referential, cur_referential)

        self.import_resources(cr, uid, ids, 'account.tax.group', context=context)

        self._bidirectional_synchro(cr, uid, external_session, obj_readable_name='LANG',
            oe_obj=self.pool.get('res.lang'),
            ps_field='language_code', ps_readable_field='name',
            oe_field='code', oe_readable_field='name',
            compare_function=self._compare_languages, context=context)

        self._bidirectional_synchro(cr, uid, external_session, obj_readable_name='COUNTRY',
            oe_obj=self.pool.get('res.country'),
            ps_field='iso_code', ps_readable_field='name',
            oe_field='code', oe_readable_field='name',
            compare_function=self._compare_countries, context=context)

        self._bidirectional_synchro(cr, uid, external_session, obj_readable_name='CURRENCY',
            oe_obj=self.pool.get('res.currency'),
            ps_field='iso_code', ps_readable_field='name',
            oe_field='name', oe_readable_field='name',
            compare_function=self._compare_currencies, context=context)

        self._bidirectional_synchro(cr, uid, external_session, obj_readable_name='TAXES',
            oe_obj=self.pool.get('account.tax'),
            ps_field='rate', ps_readable_field='name',
            oe_field='amount',
            oe_readable_field='type_tax_use',
            compare_function=self._compare_taxes, context=context)

        return True

    def _prepare_mapping_vals(self, cr, uid, referential_id, mapping_vals, context=None):
        res = super(external_referential, self)._prepare_mapping_vals(cr, uid, referential_id, mapping_vals, context=context)
        res['prestashop_primary_key'] = mapping_vals['prestashop_primary_key']
        return res

    def _prepare_mapping_fieldnames(self, cr, uid, context=None):
        res = super(external_referential, self)._prepare_mapping_fieldnames(cr, uid, context=context)
        res.append('prestashop_primary_key')
        return res

    def _prepare_mapping_template_vals(self, cr, uid, mapping, context=None):
        res = super(external_referential, self)._prepare_mapping_template_vals(cr, uid, mapping, context=context)
        res['prestashop_primary_key'] = mapping.prestashop_primary_key or ''
        return res

    def import_customers(self, cr, uid, ids, context=None):
        super(external_referential, self).import_customers(cr, uid, ids, context=context)
        self.import_resources(cr, uid, ids, 'res.partner.address', context=context)
        return True



class external_mapping(osv.osv):
    _inherit = 'external.mapping'

    _columns = {
        'prestashop_primary_key': fields.char('Prestashop primary key', size=128),
    }

class external_mapping_template(osv.osv):
    _inherit = 'external.mapping.template'

    _columns = {
        'prestashop_primary_key': fields.char('Prestashop primary key', size=128),
    }
