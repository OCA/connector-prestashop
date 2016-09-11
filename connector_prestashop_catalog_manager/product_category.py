# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.connector_prestashop.unit.exporter import (
    PrestashopExporter,
    export_record,
    TranslationPrestashopExporter
)
from openerp.addons.connector_prestashop.unit.mapper import (
    TranslationPrestashopExportMapper,
)
from openerp.addons.connector_prestashop.consumer import \
    delay_export, delay_export_all_bindings
from openerp.addons.connector_prestashop.backend import prestashop

import unicodedata
import re

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


CATEGORY_EXPORT_FIELDS = [
    'name',
    'parent_id',
    'description',
    'link_rewrite',
    'meta_description',
    'meta_keywords',
    'meta_title',
    'position']


@on_record_create(model_names='prestashop.product.category')
def prestashop_product_template_create(session, model_name, record_id, fields):
    delay_export(session, model_name, record_id, priority=20)


@on_record_write(model_names='product.category')
def product_category_write(session, model_name, record_id, fields):
    if set(fields.keys()) <= set(CATEGORY_EXPORT_FIELDS):
        delay_export_all_bindings(session, model_name, record_id, fields)


@on_record_write(model_names='prestashop.product.category')
def prestashop_product_category_write(session, model_name, record_id, fields):
    if set(fields.keys()) <= set(CATEGORY_EXPORT_FIELDS):
        delay_export(session, model_name, record_id, fields)


@prestashop
class ProductCategoryExporter(PrestashopExporter):
    _model_name = 'prestashop.product.category'

    def _create(self, record):
        res = super(ProductCategoryExporter, self)._create(record)
        return res['prestashop']['category']['id']

    def _export_dependencies(self):
        """ Export the dependencies for the category"""
        category_binder = self.binder_for('prestashop.product.category')
        categories_obj = self.session.env['prestashop.product.category']
        for category in self.erp_record:
            self.export_parent_category(
                category.odoo_id.parent_id, category_binder, categories_obj)

    def export_parent_category(self, category, binder, ps_categ_obj):
        if not category:
            return
        ext_id = binder.to_backend(category.id, wrap=True)
        if ext_id:
            return ext_id
        res = {
            'backend_id': self.backend_record.id,
            'odoo_id': category.id,
            'link_rewrite': get_slug(category.name),
        }
        category_ext_id = ps_categ_obj.with_context(
            connector_no_export=True).create(res)
        parent_cat_id = export_record(
            self.session, 'prestashop.product.category', category_ext_id.id)
        return parent_cat_id


@prestashop
class ProductCategoryExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.category'

    direct = [
        ('sequence', 'position'),
        ('default_shop_id', 'id_shop_default'),
        ('active', 'active'),
        ('position', 'position')
    ]

    @mapping
    def translatable_fields(self, record):
        translatable_fields = [
            ('name', 'name'),
            ('link_rewrite', 'link_rewrite'),
            ('description', 'description'),
            ('meta_description', 'meta_description'),
            ('meta_keywords', 'meta_keywords'),
            ('meta_title', 'meta_title'),
        ]
        trans = TranslationPrestashopExporter(self.environment)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields

    @mapping
    def parent_id(self, record):
        if not record['parent_id']:
            return {'id_parent': 2}
        category_binder = self.binder_for('prestashop.product.category')
        ext_categ_id = category_binder.to_backend(
            record.parent_id.id, wrap=True)
        return {'id_parent': ext_categ_id}
