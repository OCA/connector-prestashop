# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Alexis de Lattre <alexis.delattre@akretion.com>                   #
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
from base_external_referentials.decorator import only_for_referential, catch_error_in_report, open_report

class product_category(osv.osv):
    _inherit = 'product.category'

    _columns = {
        'is_active': fields.boolean('Active in PrestaShop'),
        'description': fields.text('Description', translate=True),
        'url_key': fields.char('Link rewrite', size=64, translate=True),
        'meta_title': fields.char('Meta title', size=128, translate=True),
        'meta_keywords': fields.text('Meta keyworks', translate=True),
        'meta_description': fields.char('Meta description', size=255, translate=True),
        }

class product_product(osv.osv):
    _inherit = 'product.product'

    @only_for_referential('prestashop')
    @open_report
    def _export_resources(self, *args, **kwargs):
        return super(product_product, self)._export_resources(*args, **kwargs)

    @only_for_referential('prestashop')
    @catch_error_in_report
    def _transform_and_send_one_resource(self, *args, **kwargs):
        return super(product_product, self)._transform_and_send_one_resource(*args, **kwargs)

    @only_for_referential('prestashop')
    def _transform_one_resource(self, cr, uid, external_session, convertion_type, resource, **kwargs):
        vals = super(product_product,self)._transform_one_resource(cr, uid, external_session, convertion_type, resource, **kwargs)
        shop = external_session.sync_from_object
        if convertion_type == 'from_openerp_to_external':
            for attribute in shop.shop_attribute_ids:
                if attribute.name in resource:
                    if attribute.ttype == 'boolean':
                        vals[attribute.external_name] = int(resource[attribute.name])
                    else:
                        vals[attribute.external_name] = resource[attribute.name]
        return vals
    
    def _get_product_feature(self, cr, uid, external_session, product_lang, langs, langs_to_ext_id, context=None):
        product_feature = []
        for group in product_lang[langs[0]].attribute_set_id.attribute_group_ids:
                    for attribute in group.attribute_ids:
                        feature_dict = {'id': self.pool.get('product.attribute').get_or_create_extid(cr, uid, external_session, attribute.attribute_id.id, context=context)}
                        if attribute.ttype == 'many2one':
                            feature_value = getattr(product_lang[langs[0]], attribute.name)
                            if feature_value:
                                feature_dict['id_feature_value'] = self.pool.get('attribute.option').get_or_create_extid(cr, uid, external_session, feature_value.id, context=context)
                            else:
                                continue
                        else:
                            feature_langs = []
                            for lang in langs:
                                feature_langs.append({'attrs': {'id': '%s'%langs_to_ext_id[lang]}, 'value': getattr(product_lang[lang], attribute.name)})
                            feature_dict.update({
                                'id_feature_value': 0,
                                'custom_feature_value': {'language': feature_langs},
                                })
                        product_feature.append(feature_dict)
        return product_feature

    def send_to_external(self, cr, uid, external_session, resources, mapping, mapping_id, update_date=None, context=None):
        langs = self.get_lang_to_export(cr, uid, external_session, context=context)
        langs_to_ext_id = {}
        for lang in langs:
            lang_id = self.pool.get('res.lang').search(cr, uid, [('code', '=', lang)], context=context)[0]
            langs_to_ext_id[lang] = self.pool.get('res.lang').get_extid(cr, uid, lang_id, external_session.referential_id.id, context=context)
        for resource_id, resource in resources.items():
            product_lang = {}
            for lang in langs:
                ctx = context.copy()
                ctx['lang'] = lang
                product_lang[lang] = self.browse(cr, uid, resource_id, context=ctx)
            product_feature = []
            if product_lang[langs[0]].attribute_set_id:
                product_feature = self._get_product_feature(cr, uid, external_session, product_lang, langs,langs_to_ext_id, context=context)
            if not resource['no_lang'].get('associations'):
                resource['no_lang']['associations'] = {}
            resource['no_lang']['associations']['product_features'] = {'product_feature': product_feature}
            if resource['no_lang'].get('accessories'):
                resource['no_lang']['associations']['accessories'] = resource['no_lang'].pop('accessories')
            if resource['no_lang'].get('categories'):
                resource['no_lang']['associations']['categories'] = resource['no_lang'].pop('categories')
        return super(product_product, self).send_to_external(cr, uid, external_session, resources,\
                                        mapping, mapping_id, update_date=update_date, context=context)
