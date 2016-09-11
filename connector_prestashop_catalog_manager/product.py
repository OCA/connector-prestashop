# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.connector_prestashop.models.product_template.importer \
    import TemplateRecordImport

from openerp.addons.connector_prestashop.unit.exporter import (
    export_record,
    TranslationPrestashopExporter
)
from openerp.addons.connector_prestashop.unit.mapper import (
    TranslationPrestashopExportMapper,
)
from openerp.addons.connector_prestashop.consumer import (
    delay_export,
    INVENTORY_FIELDS
)
from openerp.addons.connector_prestashop.backend import prestashop

import openerp.addons.decimal_precision as dp
import unicodedata
import re
from openerp import models, fields

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
def prestashop_product_template_create(session, model_name, record_id, fields):
    delay_export(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.template')
def prestashop_product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    fields = list(set(fields).difference(set(INVENTORY_FIELDS)))
    if fields:
        export_record.delay(
            session, model_name, record_id, fields, priority=20)
        # Propagate minimal_quantity from template to variants
        if 'minimal_quantity' in fields:
            ps_template = session.env[model_name].browse(record_id)
            for binding in ps_template.prestashop_bind_ids:
                binding.odoo_id.mapped(
                    'product_variant_ids.prestashop_bind_ids').write({
                        'minimal_quantity': binding.minimal_quantity
                    })


@on_record_write(model_names='product.template')
def product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.prestashop_bind_ids:
        func = "openerp.addons.connector_prestashop.unit.exporter." \
               "export_record('prestashop.product.template', %s," \
               % binding.id
        jobs = session.env['queue.job'].sudo().search(
            [('func_string', 'like', "%s%%" % func),
             ('state', 'not in', ['done', 'failed'])]
        )
        if not jobs:
            export_record.delay(
                session, 'prestashop.product.template', binding.id, fields
            )


class PrestashopProductTemplate(models.Model):
    _inherit = 'prestashop.product.template'

    meta_title = fields.Char(
        string='Meta Title',
        translate=True
    )
    meta_description = fields.Char(
        string='Meta Description',
        translate=True
    )
    meta_keywords = fields.Char(
        string='Meta Keywords',
        translate=True
    )
    tags = fields.Char(
        string='Tags',
        translate=True
    )
    online_only = fields.Boolean(string='Online Only')
    additional_shipping_cost = fields.Float(
        string='Additional Shipping Price',
        digits_compute=dp.get_precision('Product Price'),
        help="Additionnal Shipping Price for the product on Prestashop")
    available_now = fields.Char(
        string='Available Now',
        translate=True
    )
    available_later = fields.Char(
        string='Available Later',
        translate=True
    )
    available_date = fields.Date(string='Available Date')
    minimal_quantity = fields.Integer(
        string='Minimal Quantity',
        help='Minimal Sale quantity',
        default=1,
    )


@prestashop
class ProductTemplateExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.template'

    def _create(self, record):
        res = super(ProductTemplateExport, self)._create(record)
        self.write_binging_vals(self.erp_record, record)
        return res['prestashop']['product']['id']

    def _update(self, data):
        """ Update an Prestashop record """
        assert self.prestashop_id
        self.export_variants()
        self.check_images()
        self.backend_adapter.write(self.prestashop_id, data)

    def write_binging_vals(self, erp_record, ps_record):
        keys_to_update = [
            ('description_short_html', 'description_short'),
            ('description_html', 'description'),
        ]
        trans = TemplateRecordImport(self.connector_env)
        splitted_record = trans._split_per_language(ps_record)
        for lang_code, prestashop_record in splitted_record.items():
            vals = {}
            for key in keys_to_update:
                vals[key[0]] = prestashop_record[key[1]]
            erp_record.with_context(
                connector_no_export=True,
                lang=lang_code).write(vals)

    def export_categories(self, category, binder, ps_categ_obj):
        if not category:
            return
        ext_id = binder.to_backend(category.id, wrap=True)
        if ext_id:
            return ext_id
        parent_cat_id = self.export_categories(
            category.parent_id, binder, ps_categ_obj)
        position_cat_id = ps_categ_obj.search(
            [], order='position desc', limit=1)
        obj_position = position_cat_id.position + 1
        res = {
            'backend_id': self.backend_record.id,
            'odoo_id': category.id,
            'link_rewrite': get_slug(category.name),
            'position': obj_position,
        }
        category_ext_id = ps_categ_obj.with_context(
            connector_no_export=True).create(res)
        parent_cat_id = export_record(self.session,
                                      'prestashop.product.category',
                                      category_ext_id.id,
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
            self.erp_record.odoo_id.with_context(
                connector_no_export=True).write({
                    'categ_id': max_parent['categ_id'],
                    'categ_ids': [(3, max_parent['categ_id'])],
                })

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        attribute_binder = self.binder_for(
            'prestashop.product.combination.option')
        option_binder = self.binder_for(
            'prestashop.product.combination.option.value')
        category_binder = self.binder_for(
            'prestashop.product.category')
        attribute_obj = self.session.env[
            'prestashop.product.combination.option']
        categories_obj = self.session.env[
            'prestashop.product.category']
        self._set_main_category()

        for category in self.erp_record.categ_id + self.erp_record.categ_ids:
            self.export_categories(category, category_binder, categories_obj)

        for line in self.erp_record.attribute_line_ids:
            attribute_ext_id = attribute_binder.to_backend(
                line.attribute_id.id, wrap=True)
            if not attribute_ext_id:
                res = {
                    'backend_id': self.backend_record.id,
                    'odoo_id': line.attribute_id.id,
                }
                attribute_ext_id = attribute_obj.with_context(
                    connector_no_export=True).create(res)
                export_record(
                    self.session,
                    'prestashop.product.combination.option',
                    attribute_ext_id.id)
            for value in line.value_ids:
                value_ext_id = option_binder.to_backend(value.id, wrap=True)
                if not value_ext_id:
                    value_ext_id = self.session.env[
                        'prestashop.product.combination.option.value'].\
                        with_context(connector_no_export=True).create({
                            'backend_id': self.backend_record.id,
                            'odoo_id': value.id,
                        })
                    export_record(
                        self.session,
                        'prestashop.product.combination.option.value',
                        value_ext_id.id
                    )

    def export_variants(self):
        combination_obj = self.session.env['prestashop.product.combination']
        for product in self.erp_record.product_variant_ids:
            if not product.attribute_value_ids:
                continue
            combination_ext_id = combination_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('odoo_id', '=', product.id),
            ])
            if not combination_ext_id:
                combination_ext_id = combination_obj.with_context(
                    connector_no_export=True).create({
                        'backend_id': self.backend_record.id,
                        'odoo_id': product.id,
                        'main_template_id': self.binding_id,
                    })
            # If a template has been modified then always update PrestaShop
            # combinations
            export_record.delay(
                self.session,
                'prestashop.product.combination',
                combination_ext_id.id, priority=50,
                eta=timedelta(seconds=20))

    def _not_in_variant_images(self, image):
        images = []
        if len(self.erp_record.product_variant_ids) > 1:
            for product in self.erp_record.product_variant_ids:
                images.extend(product.image_ids.ids)
        return image.id not in images

    def check_images(self):
        if self.erp_record.image_ids:
            image_binder = self.binder_for('prestashop.product.image')
            for image in self.erp_record.image_ids:
                image_ext_id = image_binder.to_backend(image.id, wrap=True)
                if not image_ext_id:
                    image_ext_id = self.session.env[
                        'prestashop.product.image'].with_context(
                        connector_no_export=True).create({
                            'backend_id': self.backend_record.id,
                            'odoo_id': image.id,
                        })
                    export_record.delay(
                        self.session,
                        'prestashop.product.image',
                        image_ext_id.id, priority=15)

    def update_quantities(self):
        if len(self.erp_record.product_variant_ids) == 1:
            product = self.erp_record.odoo_id.product_variant_ids[0]
            product.update_prestashop_quantities()

    def _after_export(self):
        self.check_images()
        self.export_variants()
        self.update_quantities()


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
        ('on_sale', 'on_sale'),
    ]

    @mapping
    def list_price(self, record):
        dp_obj = self.env['decimal.precision']
        precision = dp_obj.precision_get('Product Price')
        if record.taxes_id.price_include and record.taxes_id.type == 'percent':
            return {
                'price': str(
                    round(record.list_price / (
                        1 + record.taxes_id.amount), precision))
            }
        else:
            return {'price': str(record.list_price)}

    @mapping
    def reference(self, record):
        return {'reference': record.reference or record.default_code or ''}

    def _get_product_category(self, record):
        ext_categ_ids = []
        binder = self.binder_for('prestashop.product.category')
        categories = list(set(record.categ_ids + record.categ_id))
        for category in categories:
            ext_categ_ids.append(
                {'id': binder.to_backend(category.id, wrap=True)})
        return ext_categ_ids

    @mapping
    def associations(self, record):
        return {
            'associations': {
                'categories': {
                    'category_id': self._get_product_category(record)},
            }
        }

    @mapping
    def categ_id(self, record):
        binder = self.binder_for('prestashop.product.category')
        ext_categ_id = binder.to_backend(record.categ_id.id, wrap=True)
        return {'id_category_default': ext_categ_id}

    @mapping
    def tax_ids(self, record):
        binder = self.binder_for('prestashop.account.tax.group')
        ext_id = binder.to_backend(record.tax_group_id.id, wrap=True)
        return {'id_tax_rules_group': ext_id}

    @mapping
    def available_date(self, record):
        if record.available_date:
            return {'available_date': record.available_date}
        return {}

    @mapping
    def date_add(self, record):
        # When export a record the date_add in PS is null.
        return {'date_add': record.create_date}

    @mapping
    def translatable_fields(self, record):
        translatable_fields = [
            ('name', 'name'),
            ('link_rewrite', 'link_rewrite'),
            ('meta_title', 'meta_title'),
            ('meta_description', 'meta_description'),
            ('meta_keywords', 'meta_keywords'),
            ('tags', 'tags'),
            ('available_now', 'available_now'),
            ('available_later', 'available_later'),
            ('description_short_html', 'description_short'),
            ('description_html', 'description'),
        ]

        trans = TranslationPrestashopExporter(self.connector_env)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields
