# -*- encoding: utf-8 -*-
# #############################################################################
#
#   Prestashop_catalog_manager for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#   All Rights Reserved
#   @author : Sébastien BEAU <sebastien.beau@akretion.com>
#             Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import ExportMapper, mapping
from openerp.addons.prestashoperpconnect.unit.backend_adapter import \
    PrestaShopCRUDAdapter


from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    TranslationPrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    PrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect.unit.mapper import \
    TranslationPrestashopExportMapper

from openerp.addons.prestashoperpconnect.unit.mapper import \
    PrestashopExportMapper

from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.product import INVENTORY_FIELDS
from openerp.addons.prestashoperpconnect_catalog_manager.product_combination \
    import product_product_write
from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp
from openerp.addons.prestashoperpconnect.unit.backend_adapter \
    import GenericAdapter
from openerp.tools.translate import _
import unicodedata
import re
import base64
import imghdr

try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None


def get_slug(name):
    if slugify_lib:
        try:
            return slugify_lib.slugify(name)
        except TypeError:
            pass
    uni = unicodedata.normalize('NFKD', name).encode(
        'ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[\W_]', ' ', uni).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


@on_record_create(model_names='prestashop.product.template')
def prestashop_product_template_create(session, model_name, record_id,
                                       fields):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.template')
def prestashop_product_template_write(session, model_name,
                                      record_id, fields):
    if session.context.get('connector_no_export'):
        return

    fields = list(set(fields).difference(set(INVENTORY_FIELDS)))
    if fields:
        export_record.delay(session, model_name, record_id, fields,
                            priority=20)


@on_record_write(model_names='product.template')
def product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.template', binding.id,
                            fields, priority=20)


@on_record_write(model_names='product.image')
def product_image_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.image',
                            binding.id, record.file_db_store,
                            priority=20)
    for variant in record.products:
        for variant_bind in variant.prestashop_bind_ids:
            export_record.delay(session, 'prestashop.product.combination',
                                variant_bind.id, priority=20)


class product_image(orm.Model):
    _inherit = 'product.image'

    _columns = {
        'front_image': fields.boolean(
            'Fron image',
        )}


class prestashop_product_template(orm.Model):
    _inherit = 'prestashop.product.template'

    _columns = {
        'meta_title': fields.char(
            'Meta Title',
            translate=True
        ),
        'meta_description': fields.char(
            'Meta Description',
            translate=True
        ),
        'meta_keywords': fields.char(
            'Meta Keywords',
            translate=True
        ),
        'tags': fields.char(
            'Tags',
            translate=True
        ),
        # 'available_for_order': fields.boolean(
        #     'Available For Order'
        # ),
        #        'show_price': fields.boolean(
        #            'Show Price'
        #        ),
        'online_only': fields.boolean(
            'Online Only'
        ),
        'additional_shipping_cost': fields.float(
            'Additional Shipping Price',
            digits_compute=dp.get_precision('Product Price'),
            help="Additionnal Shipping Price for the product on Prestashop"),
        'available_now': fields.char(
            'Available Now',
            translate=True
        ),
        'available_later': fields.char(
            'Available Later',
            translate=True
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
class ProductCategoryExporter(PrestashopExporter):
    _model_name = 'prestashop.product.category'


@prestashop
class ProductCategoryExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.category'

    direct = [
        ('sequence', 'position'),
        ('description', 'description'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('meta_title', 'meta_title'),
        ('default_shop_id', 'id_shop_default'),
        ('active', 'active'),
        ('position', 'position')
    ]

    @mapping
    def translatable_fields(self, record):
        translatable_fields = [
            ('name', 'name'),
            ('link_rewrite', 'link_rewrite')
        ]
        trans = TranslationPrestashopExporter(self.environment)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields

    @mapping
    def parent_id(self, record):
        if not record['parent_id']:
            return {'id_parent': 2}
        category_binder = self.get_binder_for_model(
            'prestashop.product.category')
        ext_categ_id = category_binder.to_backend(record['parent_id']['id'],
                                                  unwrap=True)
        return {'id_parent': ext_categ_id}


@prestashop
class ProductImageExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.product.image'

    direct = [
        ('file_db_store', 'content'),
        ('name', 'name'),
        ('extension', 'extension')
        # ('product_tmpl_id', 'id_product')
    ]

    @mapping
    def product_id(self, record):
        return {'id_product': record.product_id.id}


@prestashop
class ProductTemplateExport(PrestashopExporter):
    _model_name = 'prestashop.product.template'

    def _update(self, data):
        """ Update an Prestashop record """
        assert self.prestashop_id
        self.export_variants()
        self.check_images()
        self.backend_adapter.write(self.prestashop_id, data)

    def export_categories(self, category, binder, obj):
        if not category:
            return
        ext_id = binder.to_backend(category.id, unwrap=True)
        if ext_id:
            return ext_id
        parent_cat_id = self.export_categories(category.parent_id, binder, obj)
        ctx = self.session.context.copy()
        ctx['connector_no_export'] = True
        porition_cat_id = obj.search(self.session.cr, self.session.uid, [],
                                     order='position desc', limit=1,
                                     context=ctx)
        obj_position = obj.browse(self.session.cr, self.session.uid,
                                  porition_cat_id).position + 1
        res = {
            'backend_id': self.backend_record.id,
            'openerp_id': category.id,
            'link_rewrite': get_slug(category.name),
            'position': obj_position
        }
        ctx = self.session.context.copy()
        ctx['connector_no_export'] = True
        category_ext_id = obj.create(self.session.cr, self.session.uid, res,
                                     context=ctx)
        parent_cat_id = export_record(self.session,
                                      'prestashop.product.category',
                                      category_ext_id,
                                      fields={'parent_id': parent_cat_id})
        return re.search(r'\d+', parent_cat_id).group()

    def _parent_length(self, categ):
        if not categ.parent_id:
            return 1
        else:
            return 1 + self._parent_length(categ.parent_id)

    def _set_main_category(self):
        if self.erp_record.categ_id.id == 1 and self.erp_record.categ_ids:

            max_parent = {'length': 0}
            for categ in self.erp_record.categ_ids:
                parent_length = self._parent_length(categ.parent_id)
                if parent_length > max_parent['length']:
                    max_parent = {'categ_id': categ.id,
                                  'length': parent_length}
            product_obj = self.session.pool['product.template']
            ctx = self.session.context.copy()
            ctx['connector_no_export'] = True
            product_obj.write(
                self.session.cr, self.session.uid,
                self.erp_record.openerp_id.id,
                {'categ_id': max_parent['categ_id'],
                 'categ_ids': [(3, max_parent['categ_id'])]}, context=ctx)

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        attribute_binder = self.get_binder_for_model(
            'prestashop.product.combination.option')
        option_binder = self.get_binder_for_model(
            'prestashop.product.combination.option.value')
        category_binder = self.get_binder_for_model(
            'prestashop.product.category')
        attribute_obj = self.session.pool[
            'prestashop.product.combination.option']
        categories_obj = self.session.pool[
            'prestashop.product.category']
        self._set_main_category()
        for category in self.erp_record.categ_id + self.erp_record.categ_ids:
            self.export_categories(category, category_binder,
                                   categories_obj)
        for line in self.erp_record.attribute_line_ids:
            attribute_ext_id = attribute_binder.to_backend(
                line.attribute_id.id, unwrap=True)
            if not attribute_ext_id:
                ctx = self.session.context.copy()
                ctx['connector_no_export'] = True
                res = {
                    'backend_id': self.backend_record.id,
                    'openerp_id': line.attribute_id.id,
                }
                self.session.change_context({'connector_no_export': True})
                attribute_ext_id = attribute_obj.create(self.session.cr,
                                                        self.session.uid,
                                                        res)
                export_record(
                    self.session,
                    'prestashop.product.combination.option',
                    attribute_ext_id)
            for value in line.value_ids:
                value_ext_id = option_binder.to_backend(value.id,
                                                        unwrap=True)
                if not value_ext_id:
                    ctx = self.session.context.copy()
                    ctx['connector_no_export'] = True
                    value_ext_id = self.session.pool[
                        'prestashop.product.combination.option.value'].create(
                        self.session.cr, self.session.uid, {
                            'backend_id': self.backend_record.id,
                            'openerp_id': value.id}, context=ctx)
                    export_record(
                        self.session,
                        'prestashop.product.combination.option.value',
                        value_ext_id
                    )

    def export_variants(self):
        combination_obj = self.session.pool['prestashop.product.combination']
        if self.erp_record.product_variant_ids:
            ctx = self.session.context.copy()
            ctx['connector_no_export'] = True
            for product in self.erp_record.product_variant_ids:
                if not product.attribute_value_ids:
                    continue
                combination_ext_id = combination_obj.search(
                    self.session.cr, self.session.uid,
                    [('backend_id', '=', self.backend_record.id),
                     ('openerp_id', '=', product.id)], context=ctx)
#                combination_ext_id = combination_binder.to_backend(
#                    product.id, unwrap=True)
                if not combination_ext_id:
                    combination_ext_id = combination_obj.create(
                        self.session.cr, self.session.uid, {
                            'backend_id': self.backend_record.id,
                            'openerp_id': product.id,
                            'main_template_id': self.binding_id}, context=ctx)
                    export_record.delay(self.session,
                                        'prestashop.product.combination',
                                        combination_ext_id)

    def check_images(self):
        ctx = self.session.context.copy()
        ctx['connector_no_export'] = True
        # self.check_front_image(ctx)
        if self.erp_record.image_ids:
            image_binder = self.get_binder_for_model(
                'prestashop.product.image')
            for image_line in self.erp_record.image_ids:
                image_ext_id = image_binder.to_backend(image_line.id,
                                                       unwrap=True)
                if not image_ext_id:
                    image_ext_id = self.session.pool[
                        'prestashop.product.image'].create(
                        self.session.cr, self.session.uid, {
                            'backend_id': self.backend_record.id,
                            'openerp_id': image_line.id},
                        context=ctx)
                    export_record.delay(self.session,
                                        'prestashop.product.image',
                                        image_ext_id, image_line.file_db_store)
                # api.add('/images/products/xx', image_base64,
                #        img_filename='xxxxx')

    def update_quantities(self):
        if len(self.erp_record.product_variant_ids) == 1:
            self.session.pool['product.product'].update_prestashop_quantities(
                self.session.cr, self.session.uid,
                self.erp_record.openerp_id.product_variant_ids[0].id,
                context=self.session.context)

    def _after_export(self):
        self.check_images()
        self.export_variants()
        self.update_quantities()


@prestashop
class ProductImageExport(PrestashopExporter):
    _model_name = 'prestashop.product.image'

    def _run(self, fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.erp_record

        if not self.prestashop_id:
            fields = None  # should be created with all the fields

        if self._has_to_skip():
            return

        # export the missing linked resources
        self._export_dependencies()
        map_record = self.mapper.map_record(self.erp_record)

        if self.prestashop_id:
            record = map_record.values()
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self._update(record)
        else:
            # record = self.mapper.data_for_create
            record = map_record.values(for_create=True)
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self.prestashop_id = self._create(record)
            self._after_export()
        message = _('Record exported with ID %s on Prestashop.')
        return message % self.prestashop_id


@prestashop
class ProductTemplateExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.template'

    direct = [
        ('available_for_order', 'available_for_order'),
        ('show_price', 'show_price'),
        ('online_only', 'online_only'),
        ('weight', 'weight'),
        ('standard_price', 'wholesale_price'),
        ('default_shop_id', 'id_shop_default'),
        ('always_available', 'active'),
        ('ean13', 'ean13'),
        ('additional_shipping_cost', 'additional_shipping_cost'),
        ('minimal_quantity', 'minimal_quantity'),
    ]

    @mapping
    def lst_price(self, record):
        if record.taxes_id.price_include and record.taxes_id.type == 'percent':
            return {'price': record.lst_price / (1 + record.taxes_id.amount)}
        else:
            return {'price': record.lst_price}

    def _get_template_feature(self, record):
        # Buscar las product.attribute y sus valores para asociarlos al
        # producto
        template_feature = []
        attribute_binder = self.get_binder_for_model(
            'prestashop.product.combination.option')
        option_binder = self.get_binder_for_model(
            'prestashop.product.combination.option.value')
        for line in record.attribute_line_ids:
            feature_dict = {}
            attribute_ext_id = attribute_binder.to_backend(
                line.attribute_id.id, unwrap=True)
            if not attribute_ext_id:
                continue
            feature_dict = {'id': attribute_ext_id}
            values_ids = []
            for value in line.value_ids:
                value_ext_id = option_binder.to_backend(value.id,
                                                        unwrap=True)
                if not value_ext_id:
                    continue
                values_ids.append(value_ext_id)
            res = {'id_feature_value': values_ids}
            feature_dict.update(res)
            template_feature.append(feature_dict)
        return template_feature

    @mapping
    def reference(self, record):
        if record.reference:
            return {'reference': record.reference}
        else:
            return {'reference': record.default_code}

    def _get_product_category(self, record):
        ext_categ_ids = []
        binder = self.get_binder_for_model('prestashop.product.category')
        categories = list(set(record.categ_ids + record.categ_id))
        for category in categories:
            ext_categ_ids.append(
                {'id': binder.to_backend(category.id, unwrap=True)})
        return ext_categ_ids

    @mapping
    def associations(self, record):
        return {
            'associations': {
                'categories': {
                    'category_id': self._get_product_category(record)},
                'product_features': {
                    'product_feature': self._get_template_feature(record)},
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

    @mapping
    def translatable_fields(self, record):
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
            ("description_sale", "description"),
            ('description', 'description_short'),
        ]
        trans = TranslationPrestashopExporter(self.environment)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields
