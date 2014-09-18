# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2013 Akretion                                               #
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

from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    TranslationPrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect.unit.mapper \
    import TranslationPrestashopExportMapper
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.product import INVENTORY_FIELDS
from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp


@on_record_create(model_names='prestashop.product.product')
def prestashop_product_product_create(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.product')
def prestashop_product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    fields = list(set(fields).difference(set(INVENTORY_FIELDS)))
    if fields:
        export_record.delay(
            session, model_name, record_id, fields, priority=20)


@on_record_write(model_names='product.product')
def product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(
        session.cr, session.uid, record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(
            session, 'prestashop.product.product', binding.id, fields,
            priority=20)


class prestashop_product_product(orm.Model):
    _inherit = 'prestashop.product.product'

    _columns = {
        'meta_title': fields.char(
            'Meta Title',
            translate=True,
        ),
        'meta_description': fields.char(
            'Meta Description',
            translate=True,
        ),
        'meta_keywords': fields.char(
            'Meta Keywords',
            translate=True,
        ),
        'tags': fields.char(
            'Tags',
            translate=True,
        ),
        'available_for_order': fields.boolean(
            'Available For Order'
        ),
        'show_price': fields.boolean(
            'Show Price'
        ),
        'online_only': fields.boolean(
            'Online Only'
        ),
        'additional_shipping_cost': fields.float(
            'Additional Shipping Price',
            digits_compute=dp.get_precision('Product Price'),
            help="Additionnal Shipping Price for the product on Prestashop"),
        'available_now': fields.char(
            'Available Now',
            translate=True,
        ),
        'available_later': fields.char(
            'Available Later',
            translate=True,
        ),
        'available_date': fields.date(
            'Available Date'
        ),
        'minimal_quantity': fields.integer(
            'Minimal Quantity',
            help='Minimal Sale quantity',
        ),
    }

    _defaults = {
        'minimal_quantity': 1,
    }


@prestashop
class ProductExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.product'

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        # TODO add export of category
        attribute_binder = self.get_binder_for_model(
            'prestashop.product.attribute')
        option_binder = self.get_binder_for_model(
            'prestashop.attribute.option')
        for group in self.erp_record.attribute_group_ids:
            for attribute in group.attribute_ids:
                attribute_ext_id = attribute_binder.to_backend(
                    attribute.attribute_id.id, unwrap=True)
                if not(attribute_ext_id and attribute.ttype == 'many2one'):
                    break
                option = self.erp_record[attribute.name]
                if not (option and not option_binder.to_backend(
                        option.id, unwrap=True)):
                    break
                ctx = self.session.context.copy()
                ctx['connector_no_export'] = True
                pao_obj = self.session.pool['prestashop.attribute.option']
                binding_id = pao_obj.create(
                    self.session.cr, self.session.uid, {
                        'backend_id': self.backend_record.id,
                        'openerp_id': option.id,
                    }, context=ctx)
                export_record(
                    self.session, 'prestashop.attribute.option', binding_id)


@prestashop
class ProductExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.product'

    direct = [
        ('lst_price', 'price'),
        ('available_for_order', 'available_for_order'),
        ('show_price', 'show_price'),
        ('online_only', 'online_only'),
        ('weight', 'weight'),
        ('standard_price', 'wholesale_price'),
        ('default_code', 'reference'),
        ('default_shop_id', 'id_shop_default'),
        ('active', 'active'),
        ('ean13', 'ean13'),
        ('additional_shipping_cost', 'additional_shipping_cost'),
        ('minimal_quantity', 'minimal_quantity'),
    ]

    translatable_fields = [
        ('name', 'name'),
        ('link_rewrite', 'link_rewrite'),
        ('meta_title', 'meta_title'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('tags', 'tags'),
        ('description_short_html', 'description_short'),
        ('description_html', 'description'),
        ('available_now', 'available_now'),
        ('available_later', 'available_later'),
    ]

    def _get_product_feature(self, record):
        product_feature = []
        attribute_binder = self.get_binder_for_model(
            'prestashop.product.attribute')
        option_binder = self.get_binder_for_model(
            'prestashop.attribute.option')
        for group in record.attribute_group_ids:
            for attribute in group.attribute_ids:
                attribute_ext_id = attribute_binder.to_backend(
                    attribute.attribute_id.id, unwrap=True)
                if not attribute_ext_id:
                    continue
                feature_dict = {'id': attribute_ext_id}
                if attribute.ttype == 'many2one':
                    option = record[attribute.name]
                    if option:
                        feature_dict['id_feature_value'] = \
                            option_binder.to_backend(option.id, unwrap=True)
                    else:
                        continue
                else:
                    feature_dict['id_feature_value'] = 0
                    if attribute.translate:
                        res = self.convert_languages(
                            [(attribute.name, 'custom_feature_value')])
                    else:
                        res = {'custom_feature_value': record[attribute.name]}
                    feature_dict.update(res)
                product_feature.append(feature_dict)
        return product_feature

    def _get_product_category(self, record):
        ext_categ_ids = []
        binder = self.get_binder_for_model('prestashop.product.category')
        categories = record.categ_ids + [record.categ_id]
        for category in categories:
            ext_categ_ids.append(
                {'id': binder.to_backend(category.id, unwrap=True)}
                )
        return ext_categ_ids

    @mapping
    def associations(self, record):
        return {
            'associations': {
                'categories': {
                    'category_id': self._get_product_category(record)},
                'product_features': {
                    'product_feature': self._get_product_feature(record)},
                }
            }

    @mapping
    def categ_id(self, record):
        binder = self.get_binder_for_model('prestashop.product.category')
        ext_categ_id = binder.to_backend(record.categ_id.id, unwrap=True)
        return {'id_category_default': ext_categ_id}

    @mapping
    def tax_ids(self, record):
        binder = self.get_binder_for_model('prestashop.account.tax.group')
        ext_id = binder.to_backend(record.tax_group_id.id, unwrap=True)
        return {'id_tax_rules_group': ext_id}

    @mapping
    def available_date(self, record):
        if record.available_date:
            return {'available_date': record.available_date}
        return {}
