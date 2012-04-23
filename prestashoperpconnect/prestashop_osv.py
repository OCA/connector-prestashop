# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Authors :                                                                 #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Mathieu VATEL <mathieu@julius.fr>                                 #
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
        search_vals = [('model', '=', self._name), ('referential_id', '=', external_session.referential_id.id)]
        mapping_ids = self.pool.get('external.mapping').search(cr, uid, search_vals)
        if mapping is None:
            mapping = {mapping_ids[0] : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
        ext_resource = mapping[mapping_ids[0]]['external_resource_name']
        return external_session.connection.search(ext_resource, options = resource_filter)

    @only_for_referential('prestashop')
    def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, mapping=None, fields=None, context=None):
        search_vals = [('model', '=', self._name), ('referential_id', '=', external_session.referential_id.id)]
        mapping_ids = self.pool.get('external.mapping').search(cr, uid, search_vals)
        if mapping is None:
            mapping = {mapping_ids[0] : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
        lang_resource = {}
        main_data = {}
        ext_resource = mapping[mapping_ids[0]]['external_resource_name']
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
    def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None, mapping=None, mapping_id=None, context=None):
        lang_obj = self.pool.get('res.lang')
        ext_lang_id = resource.get('ext_lang_id', False)
        if ext_lang_id:
            oe_lang_id = lang_obj.extid_to_existing_oeid(cr, uid, external_session.referential_id.id, ext_lang_id, context=context)
            if oe_lang_id:
                lang = lang_obj.read(cr, uid, oe_lang_id, ['code'], context=context)
                context['lang'] = lang['code']
        return super(prestashop_osv, self)._record_one_external_resource(cr, uid, external_session, \
                        resource, defaults=defaults, mapping=mapping, context=context)
    
    def transform_one_resource_to_prestashop_vals(self, cr, uid, external_session, resource, external_data, method='add', context=None):
        if context == None:
            context = {}
        lang_obj = self.pool.get('res.lang')
        resource_data = {}
        key = external_data.keys()[0]
        resource_data[key] = {}
        if method == 'edit':
            external_id = external_data[key]['id']
        for data_value in external_data[key]:
            if isinstance(external_data[key][data_value],dict):
                if 'language' in external_data[key][data_value]:
                    resource_data[key][data_value] = {}
                    resource_data[key][data_value]['language'] = external_data[key][data_value]['language']
                    lang_vals = resource_data[key][data_value]['language']
                    new_lang_vals = []
                    for vals in lang_vals:
                        if 'value' in vals:
                            vals['value'] = ''
                        if 'attrs' in vals:
                            if 'id' in vals['attrs']:
                                ext_lang_id = vals['attrs'].get('id',False)
                                oe_lang_id = lang_obj.extid_to_existing_oeid(cr, uid, external_session.referential_id.id, \
                                            ext_lang_id, context=context)
                                if oe_lang_id:
                                    lang = lang_obj.read(cr, uid, oe_lang_id, ['code'], context=context)
                                    if lang['code'] in resource:
                                        vals['value'] = resource[lang['code']].get(data_value,False) or ''
                                    if not vals['value'] and 'en_US' in resource and data_value in resource['en_US']:
                                        vals['value'] = resource['en_US'].get(data_value,False) or ''
                        new_lang_vals.append(vals)
                    resource_data[key][data_value]['language'] = new_lang_vals
            else:
                if data_value in resource['en_US']:
                    resource_data[key][data_value] = str(resource['en_US'][data_value])
                else:
                    resource_data[key][data_value] = ''
        if method == 'edit':
            resource_data[key]['id'] = external_id
        return resource_data
    
    @only_for_referential('prestashop')
    def ext_create(self, cr, uid, external_session, resources, context=None):
        search_vals = [('model', '=', self._name), ('referential_id', '=', external_session.referential_id.id)]
        mapping_ids = self.pool.get('external.mapping').search(cr, uid, search_vals, context=context)
        mapping = {mapping_ids[0] : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
        ext_resource = mapping[mapping_ids[0]]['external_resource_name']
        ext_ids = external_session.connection.search(ext_resource, options={'limit': [0,1]})
        external_data = external_session.connection.get(ext_resource, resource_id=ext_ids[0])
        external_ids = {}
        for existing_rec_id in resources.keys():
            resource = resources[existing_rec_id]
            resource_data = self.transform_one_resource_to_prestashop_vals(cr, uid, external_session, resource,\
                                    external_data, method='add', context=context)
#            associations = {'categories':{},'images':{},'combinations':{},'product_option_values':{},'product_features':{}}
#            resource_data.update({'associations':associations})
            result = external_session.connection.add(ext_resource, resource_data)
            external_id = result.get('prestashop',False) and \
                        result['prestashop'].get('product',False) and \
                        result['prestashop']['product'].get('id',False)
            if external_id:
                external_ids.update({existing_rec_id : external_id})
        return external_ids
    
    @only_for_referential('prestashop')
    def ext_update(self, cr, uid, external_session, resources, context=None):
        search_vals = [('model', '=', self._name), ('referential_id', '=', external_session.referential_id.id)]
        mapping_ids = self.pool.get('external.mapping').search(cr, uid, search_vals, context=context)
        mapping = {mapping_ids[0] : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
        ext_resource = mapping[mapping_ids[0]]['external_resource_name']
        for existing_rec_id in resources.keys():
            ext_id = self.oeid_to_existing_extid(cr, uid, external_session.referential_id.id, existing_rec_id, context=context)
            external_data = external_session.connection.get(ext_resource, resource_id=ext_id)
            resource = resources[existing_rec_id]
            resource_data = self.transform_one_resource_to_prestashop_vals(cr, uid, external_session, resource, \
                                    external_data, method='edit', context=context)
            result = external_session.connection.edit(ext_resource, ext_id, resource_data)
        return False
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
