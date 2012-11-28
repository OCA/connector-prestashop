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
from prestapyt import PrestaShopWebServiceError
from tools.translate import _
import logging

_logger = logging.getLogger(__name__)

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


    def call_prestashop_method(self, cr, uid, external_session, resource_id, resource, method, mapping=None, mapping_id=None, context=None):
        # Remove the fields for image in resource dict
        image_binary = resource['category'].pop('image_binary')
        image_filename = resource['category'].pop('image_filename')
        _logger.info('Product category: sync regular data first')
        res = super(product_category, self).call_prestashop_method(cr, uid, external_session, resource, method, mapping=mapping, mapping_id=mapping_id, context=context)
        # take care of IMAGE now
        # If the method is edit, I always delete and re-create the image
        if method == 'edit':
            ps_categ_ids_with_images = external_session.connection.search('images/' + mapping[mapping_id]['external_resource_name'])
            if ps_categ_ids_with_images and resource['category'].get('id') in ps_categ_ids_with_images:
                # Delete the image
                external_session.connection.delete('images/' + mapping[mapping_id]['external_resource_name'], resource['category'].get('id'))
        if image_binary:
            _logger.info('Product category: sync image %s' % image_filename)
            try:
                # Create the image
                res = getattr(external_session.connection, mapping[mapping_id]['external_create_method'] or 'add')('images/' + mapping[mapping_id]['external_resource_name'] + '/' + str(resource['category'].get('id')), image_binary, img_filename=image_filename)
            except PrestaShopWebServiceError, e:
                _logger.warning("PrestaShop webservice answered an error on upload of image category. HTTP error code: %s, PrestaShop error code: %s, PrestaShop error message: %s" % (e.error_code, e.ps_error_code, e.ps_error_msg))
                raise osv.except_osv(_('PrestaShop Webservice Error:'), e.ps_error_msg)
        return res


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
