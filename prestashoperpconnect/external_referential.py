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
from tools.translate import _
from base_external_referentials.decorator import only_for_referential
from prestapyt import PrestaShopWebServiceError, PrestaShopWebService, PrestaShopWebServiceDict
from prestashop_osv import prestashop_osv
import logging
_logger = logging.getLogger(__name__)

class external_referential(prestashop_osv):
    _inherit = "external.referential"
    
    @only_for_referential('prestashop')
    def external_connection(self, cr, uid, id, DEBUG=False, context=None):
        if isinstance(id, list):
            id=id[0]
        referential = self.browse(cr, uid, id, context=context)
        prestashop = PrestaShopWebServiceDict('%s/api'%referential.location, referential.apipass)
        try:        
            prestashop.head('')
        except Exception, e:
            raise osv.except_osv(_("Connection Error"), _("Could not connect to server\nCheck url & password.\n %s"%e))
        return prestashop

    @only_for_referential('prestashop')
    def _import_resources(self, cr, uid, ref_called_from, referential_id, defaults, context=None, method="search_then_read"):
        if context is None:
            context = {}
        print 'start'
        _logger.info(_("Starting to create the Prestashop referential"))
        print 'I will maimport the referential'
        #TODO create shop (what we should do for version older than 1.5) + group shop + languages
        print "context=", context
        #referential_id = context.get('referential_id', False)
        if not referential_id: raise osv.except_osv(_('Error :'), 'Hara kiri missing referential')
        _logger.info(_("Starting synchro of languages between OERP and PS"))
        # Loop on OERP res.lang
        lang_obj = self.pool.get('res.lang')
        oe_lang_ids = lang_obj.search(cr, uid, [], context=context)
        oe_langs = lang_obj.read(cr, uid, oe_lang_ids, ['code', 'name'], context=context)
        print "oe_langs=", oe_langs
        # Get the language IDS from PS
        mapping = {lang_obj._name : lang_obj._get_mapping(cr, uid, referential_id, context=context)}
        res_ps_lang = lang_obj._get_external_resource_ids(cr, uid, ref_called_from=None, referential_id=referential_id, resource_filter=None, mapping=mapping, context=context)
        print "res_ps_lang=", res_ps_lang

        ps_lang_list = []
        for ps_lang in res_ps_lang:
            ps_lang_list.append(ps_lang['attrs']['id'])
        print "ps_lang_list =", ps_lang_list
        for ps_lang_id in ps_lang_list:
            # Do nothing for the IDs already mapped            pour tous les IDs déjà mappés, je fais rien... (fonction _extid_to_existing_oeid - False si rien)
            oe_lang_id = lang_obj.extid_to_existing_oeid(cr, uid, external_id=ps_lang_id, referential_id=referential_id, context=context)
            print "oe_lang_id=", oe_lang_id
            if oe_lang_id:
                _logger.info(_("PS lang ID %s is already mapped to OERP lang ID %s") %(ps_lang_id, oe_lang_id))
            else:
                # Now I try to match between OERP and PS
                # I read field in PS
                ps_lang_dict = lang_obj._get_external_resources(cr, uid, ref_called_from=None, mapping=mapping, referential_id=referential_id, ext_id=ps_lang_id, context=context)
                print "ps_lang_dict=", ps_lang_dict
                for oe_lang in oe_langs: # Loop on OE langs
                    if len(oe_lang['code']) >= 2 and len(ps_lang_dict[0]['language_code']) >=2:
                        if oe_lang['code'][0:2] == ps_lang_dict[0]['language_code'][0:2]:
                        # it matches, so I write the external ID
                            lang_obj.create_external_id_vals(cr, uid, existing_rec_id=oe_lang['id'], external_id=ps_lang_id, referential_id=referential_id, context=context)
                            _logger.info(_("Mapping PS lang '%s' (%s) to OERP lang '%s' (%s)") %(ps_lang_dict[0]['name'], ps_lang_dict[0]['language_code'], oe_lang['name'], oe_lang['code']))
                    else:
                        _logger.warning(_("PS lang '%s' (%s) was not mapped to any OERP lang") %(ps_lang_dict[0]['name'], ps_lang_dict[0]['language_code']))
        _logger.info(_("Synchro of languages between OERP and PS successfull"))
        return {}

class res_lang(prestashop_osv):
    _inherit='res.lang'

