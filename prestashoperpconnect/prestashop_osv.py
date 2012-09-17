    # -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Authors :                                                                 #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Mathieu VATEL <mathieu@julius.fr>                                 #
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
from base_external_referentials.decorator import only_for_referential, commit_now
from base_external_referentials.external_osv import override, extend
from collections import defaultdict
from tools.translate import _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

@extend(osv.osv)
@only_for_referential('prestashop')
def get_resources_with_lang(self, cr, uid, external_session, resources, primary_key, context=None):
    new_resources = {}
    for resource_id, resource in resources.items():
        new_resource = {}
        for lang, fields in resource.items():
            if lang == 'no_lang':
                if resource['no_lang'].get('ext_id'):
                    resource['no_lang']['id'] = resource['no_lang'].pop('ext_id')
                new_resource.update(resource['no_lang'])
            else:
                lang_id = self.pool.get('res.lang').search(cr, uid, [('code', '=', lang)], context=context)[0]
                presta_id = self.pool.get('res.lang').get_extid(cr, uid, lang_id, external_session.referential_id.id, context=context)
                for field, value in fields.items():
                    if field == 'ext_id':
                        continue
                    lang_and_value = {'attrs': {'id': '%s' %presta_id}, 'value': value}
                    if not new_resource.get(field):
                        new_resource[field] = {'language' : [lang_and_value]}
                    else:
                        new_resource[field]['language'].append(lang_and_value)
        new_resources[resource_id] = {primary_key : new_resource}
    return new_resources

@override(osv.osv, 'prestashop_')
@only_for_referential('prestashop')
def ext_create(self, cr, uid, external_session, resources, mapping=None, mapping_id=None, context=None):
    res = {}
    mapping, mapping_id = self._init_mapping(cr, uid, external_session.referential_id.id, mapping=mapping, mapping_id=mapping_id, context=context)
    primary_key = mapping[mapping_id]['prestashop_primary_key']
    presta_resources = self.get_resources_with_lang(cr, uid, external_session, resources, primary_key, context=context)
    for resource_id, resource in presta_resources.items():
        res[resource_id] = getattr(external_session.connection, mapping[mapping_id]['external_create_method'] or 'add')(mapping[mapping_id]['external_resource_name'], resource)
    return res

@override(osv.osv, 'prestashop_')
@only_for_referential('prestashop')
def ext_update(self, cr, uid, external_session, resources, mapping=None, mapping_id=None, context=None):
    res = {}
    mapping, mapping_id = self._init_mapping(cr, uid, external_session.referential_id.id, mapping=mapping, mapping_id=mapping_id, context=context)
    primary_key = mapping[mapping_id]['prestashop_primary_key']
    presta_resources = self.get_resources_with_lang(cr, uid, external_session, resources, primary_key, context=context)
    for resource_id, resource in presta_resources.items():
        res[resource_id] = getattr(external_session.connection, mapping[mapping_id]['external_update_method'] or 'edit')(mapping[mapping_id]['external_resource_name'], resource)
    return res

@override(osv.osv, 'prestashop_')
@only_for_referential('prestashop')
def get_lang_to_export(self, cr, uid, external_session, context=None):
    res = []
    for lang in external_session.referential_id.active_language_ids:
        res.append(lang.code)
    if not res:
        raise osv.except_osv(_("Configuration Error"), _("You need to define on the external referential prestashop the different languages of prestashop (page : Configuration)!"))
    return res

@extend(osv.osv)
@only_for_referential('prestashop')
def _get_last_imported_date(self, cr, uid, external_session, context=None):
    return False

@extend(osv.osv)
@only_for_referential('prestashop')
def _set_last_imported_date(self, cr, uid, external_session, date, context=None):
    return True

@override(osv.osv, 'prestashop_')
@only_for_referential('prestashop')
def _get_filter(self, cr, uid, external_session, step, previous_filter=None, context=None):
    """
    Used to limit the query in external library
    :param ExternalSession external_session : External_session that contain all params of connection
    :param int step: Step the of the import, 100 meant you will import data per 100
    :param dict previous_filter: the previous filter
    :return: dictionary with a filter
    :rtype: dict
    """
    if not previous_filter:
        start = 0
    else:
        start = sum([int(x) for x in previous_filter['limit'].split(',')])
    resource_filter = {
        'limit': "%s,%s"%(start,step),
    }
    last_export = self._get_last_imported_date(cr, uid, external_session, context=context)
    self._set_last_imported_date(cr, uid, external_session, date='default', context=context)
    if last_export:
        date = datetime.strptime(last_export,  DEFAULT_SERVER_DATETIME_FORMAT)
        resource_filter['date_filter'] = [['date_upd', '>', date]]
    return resource_filter

@override(osv.osv, 'prestashop_')
@only_for_referential('prestashop')
def _get_external_resource_ids(self, cr, uid, external_session, resource_filter=None, mapping=None, context=None):
    search_vals = [('model', '=', self._name), ('referential_id', '=', external_session.referential_id.id)]
    mapping_ids = self.pool.get('external.mapping').search(cr, uid, search_vals)
    if mapping is None:
        mapping = {mapping_ids[0] : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
    ext_resource = mapping[mapping_ids[0]]['external_resource_name']
    return external_session.connection.search(ext_resource, options = resource_filter)

@override(osv.osv, 'prestashop_')
@only_for_referential('prestashop')
def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, mapping=None, fields=None, context=None):
    #TODO begin refactor with _get_external_resource_ids()
    search_vals = [('model', '=', self._name), ('referential_id', '=', external_session.referential_id.id)]
    mapping_ids = self.pool.get('external.mapping').search(cr, uid, search_vals)
    if mapping is None:
        mapping = {mapping_ids[0] : self._get_mapping(cr, uid, external_session.referential_id.id, context=context)}
    # end refactor
    lang_resource = {}
    main_data = {}
    ext_resource = mapping[mapping_ids[0]]['external_resource_name']
    resource = external_session.connection.get(ext_resource, external_id)
    resource = resource[resource.keys()[0]]
    for key in resource:
        if key == 'associations':
            for key_one in resource[key].keys():
                key_two = [key_two for key_two in resource[key][key_one].keys() if key_two != 'attrs'][0]
                vals = resource[key][key_one][key_two]
                if isinstance(vals, dict):
                    vals = [vals]
                main_data[key_one] = [int(val['id']) for val in vals]
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

@override(osv.osv, 'prestashop_')
@only_for_referential('prestashop')
def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None, mapping=None, mapping_id=None, context=None):
    lang_obj = self.pool.get('res.lang')
    ext_lang_id = resource.get('ext_lang_id', False)
    if ext_lang_id:
        oe_lang_id = lang_obj.extid_to_existing_oeid(cr, uid, external_session.referential_id.id, ext_lang_id, context=context)
        if oe_lang_id:
            lang = lang_obj.read(cr, uid, oe_lang_id, ['code'], context=context)
            context['lang'] = lang['code']
    return self.prestashop__record_one_external_resource(cr, uid, external_session, \
                    resource, defaults=defaults, mapping=mapping, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
