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
import netsvc
from base_external_referentials.decorator import only_for_referential
from collections import defaultdict

class prestashop_osv(osv.osv):
    _register = False

    @only_for_referential('prestashop')
    def _get_filter(self, cr, uid, external_session, step, previous_filter=None, context=None):
        if not previous_filter:
            start = 0
        else:
            start = sum([int(x) for x in previous_filter['limit'].split(',')])
        resource_filter = {
            'limit': "%s,%s"%(start,step),
        }
        return resource_filter


    @only_for_referential('prestashop')
    def _get_external_resource_ids(self, cr, uid, external_session, resource_filter=None, mapping=None, context=None):
        if mapping is None:
            mapping = {self._name : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
        ext_resource = mapping[self._name]['external_resource_name']
        return external_session.connection.search(ext_resource, options = resource_filter)

    @only_for_referential('prestashop')
    def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, mapping=None, fields=None, context=None):
        if mapping is None:
            mapping = {self._name : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
        lang_resource = {}
        main_data = {}
        ext_resource = mapping[self._name]['external_resource_name']
        resource = external_session.connection.get(ext_resource, external_id)
        resource = resource[resource.keys()[0]]
        for key in resource:
            if key == 'associations':
                key_one = resource[key].keys()[0]
                key_two = resource[key][key_one].keys()[0]
                main_data[key_one] = resource[key][key_one][key_two]
            elif isinstance(resource[key], dict) and resource[key].get('language'):
                lang_vals = resource[key]['language']
                if not isinstance(lang_vals, list):
                    lang_vals = [lang_vals]
                for lang_val in lang_vals:
                    lang_id = lang_val['attrs']['id']
                    if not lang_resource.get(str(lang_id)):
                        lang_resource[str(lang_id)] = {'ext_lang_id': lang_id, 'id': resource['id']}
                    lang_resource[str(lang_id)][key] = lang_val['value']
            elif isinstance(resource[key], dict) and resource[key].get('attrs'):
                main_data[key] = resource[key]['value']
            else:
                main_data[key] = resource[key]
        #TODO Improve when the lang will be mapped
        lang_ids = lang_resource.keys()
        if lang_ids:
            main_lang_id = lang_ids.pop()
            main_data.update(lang_resource[main_lang_id])
            main_data.update({'ext_lang_id': main_lang_id})
        result = [main_data]
        for lang_id in lang_ids:            
            result.append(lang_resource[lang_id])
        return result

    @only_for_referential('prestashop')
    def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None, mapping=None, context=None):
        lang_obj = self.pool.get('res.lang')
        ext_lang_id = resource.get('ext_lang_id', False)
        if ext_lang_id:
            oe_lang_id = lang_obj.extid_to_existing_oeid(cr, uid, ext_lang_id, external_session.referential_id.id, context=context)
            if oe_lang_id:
                lang = lang_obj.read(cr, uid, oe_lang_id, ['code'], context=context)
                context['lang'] = lang['code']
        return super(prestashop_osv, self)._record_one_external_resource(cr, uid, external_session, resource, defaults=defaults, mapping=mapping, context=context)

