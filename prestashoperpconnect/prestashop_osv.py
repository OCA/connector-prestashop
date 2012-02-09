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
    def _get_filter(self, cr, uid, ref_called_from, referential_id, resource_filter, step, context=None):
        if not resource_filter:
            start = 0
        else:
            start = sum([int(x) for x in resource_filter['limit'].split(',')])
        resource_filter = {
            'limit': "%s,%s"%(start,step),
        }
        print 'resource_filter', resource_filter
        return resource_filter


    @only_for_referential('prestashop')
    def _get_external_resource_ids(self, cr, uid, ref_called_from, referential_id, resource_filter, mapping, context=None):
        conn = context['conn']
        ext_resource = mapping[self._name]['external_resource_name']
        print "Import data for %s with filter %s"%(ext_resource, resource_filter)
        ext_ids = conn.get(ext_resource, options = resource_filter)
        print 'ext_ids', ext_ids
        if isinstance(ext_ids[ext_resource], dict):
            key = ext_ids[ext_resource].keys()[0]
            return ext_ids[ext_resource][key]
        return []

    @only_for_referential('prestashop')
    def _get_external_resources(self, cr, uid, ref_called_from, mapping, referential_id, ext_id, context):
        lang_resource = {}
        main_data = {}
        conn = context['conn']
        ext_resource = mapping[self._name]['external_resource_name']
        resource = conn.get(ext_resource, ext_id)
        resource = resource[resource.keys()[0]]
        for key in resource:
            if isinstance(resource[key], dict) and resource[key].get('language'):
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
        main_lang_id = lang_ids.pop()
        main_data.update(lang_resource[main_lang_id])
        main_data.update({'ext_lang_id': main_lang_id})
        result = [main_data]
        for lang_id in lang_ids:            
            result.append(lang_resource[lang_id])
        return result

    @only_for_referential('prestashop')
    def _record_one_external_resource(self, cr, uid, row, referential_id, defaults=None, context=None, mapping=None):
        #TODO map lang
        ext_lang_id = row['ext_lang_id']
        lang_dict = {'2' : 'fr_FR', '1' : 'en_US'}
        context['lang'] = lang_dict[ext_lang_id]
        print 'context', context
        return super(prestashop_osv, self)._record_one_external_resource(cr, uid, row, referential_id, defaults=defaults, context=context, mapping=mapping)

