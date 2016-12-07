# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from openerp.addons.connector.unit.mapper import mapping, m2o_to_backend

from openerp.addons.connector_prestashop.\
    models.product_template.importer import ProductTemplateImporter

from openerp.addons.connector_prestashop.unit.exporter import (
    export_record,
    TranslationPrestashopExporter
)
from openerp.addons.connector_prestashop.unit.mapper import (
    TranslationPrestashopExportMapper,
)
from openerp.addons.connector_prestashop.backend import prestashop
from ...consumer import get_slug


@prestashop
class ProductTemplateExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.template'

    def _create(self, record):
        res = super(ProductTemplateExport, self)._create(record)
        self.write_binging_vals(self.binding, record)
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
        trans = ProductTemplateImporter(self.connector_env)
        splitted_record = trans._split_per_language(ps_record)
        for lang_code, prestashop_record in splitted_record.items():
            vals = {}
            for key in keys_to_update:
                vals[key[0]] = prestashop_record[key[1]]
            erp_record.with_context(
                connector_no_export=True,
                lang=lang_code).write(vals)

    def export_categories(self, category):
        if not category:
            return
        category_binder = self.binder_for('prestashop.product.category')
        ext_id = category_binder.to_backend(category.id, wrap=True)
        if ext_id:
            return ext_id

        ps_categ_obj = self.session.env['prestashop.product.category']
        position_cat_id = ps_categ_obj.search(
            [], order='position desc', limit=1)
        obj_position = position_cat_id.position + 1
        res = {
            'backend_id': self.backend_record.id,
            'odoo_id': category.id,
            'link_rewrite': get_slug(category.name),
            'position': obj_position,
        }
        binding = ps_categ_obj.with_context(
            connector_no_export=True).create(res)
        export_record(
            self.session,
            'prestashop.product.category',
            binding.id)

    def _parent_length(self, categ):
        if not categ.parent_id:
            return 1
        else:
            return 1 + self._parent_length(categ.parent_id)

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        super(ProductTemplateExport, self)._export_dependencies()
        attribute_binder = self.binder_for(
            'prestashop.product.combination.option')
        option_binder = self.binder_for(
            'prestashop.product.combination.option.value')

        for category in self.binding.categ_ids:
            self.export_categories(category)

        for line in self.binding.attribute_line_ids:
            attribute_ext_id = attribute_binder.to_backend(
                line.attribute_id.id, wrap=True)
            if not attribute_ext_id:
                self._export_dependency(
                    line.attribute_id,
                    'prestashop.product.combination.option')
            for value in line.value_ids:
                value_ext_id = option_binder.to_backend(value.id, wrap=True)
                if not value_ext_id:
                    self._export_dependency(
                        value, 'prestashop.product.combination.option.value')

    def export_variants(self):
        combination_obj = self.session.env['prestashop.product.combination']
        for product in self.binding.product_variant_ids:
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
        if len(self.binding.product_variant_ids) > 1:
            for product in self.binding.product_variant_ids:
                images.extend(product.image_ids.ids)
        return image.id not in images

    def check_images(self):
        if self.binding.image_ids:
            image_binder = self.binder_for('prestashop.product.image')
            for image in self.binding.image_ids:
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
        if len(self.binding.product_variant_ids) == 1:
            product = self.binding.odoo_id.product_variant_ids[0]
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
        (m2o_to_backend('default_shop_id'), 'id_shop_default'),
        ('always_available', 'active'),
        ('barcode', 'barcode'),
        ('additional_shipping_cost', 'additional_shipping_cost'),
        ('minimal_quantity', 'minimal_quantity'),
        ('on_sale', 'on_sale'),
        (m2o_to_backend(
            'prestashop_default_category_id',
            binding='prestashop.product.category'), 'id_category_default'),
    ]
    # handled by base mapping `translatable_fields`
    _translatable_fields = [
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

    def _get_factor_tax(self, tax):
        factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
        return factor_tax

    @mapping
    def list_price(self, record):
        dp_obj = self.env['decimal.precision']
        precision = dp_obj.precision_get('Product Price')
        tax = record.taxes_id
        if tax.price_include and tax.amount_type == 'percent':
            return {
                'price': str(
                    round(record.list_price /
                          self._get_factor_tax(tax), precision))
            }
        else:
            return {'price': str(record.list_price)}

    @mapping
    def reference(self, record):
        return {'reference': record.reference or record.default_code or ''}

    def _get_product_category(self, record):
        ext_categ_ids = []
        binder = self.binder_for('prestashop.product.category')
        for category in record.categ_ids:
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
    def tax_ids(self, record):
        if not record.taxes_id:
            return
        binder = self.binder_for('prestashop.account.tax.group')
        ext_id = binder.to_backend(record.taxes_id[:1].tax_group_id, wrap=True)
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
    def default_image(self, record):
        default_image = record.image_ids.filtered('front_image')[:1]
        if default_image:
            binder = self.binder_for('prestashop.product.image')
            ps_image_id = binder.to_backend(default_image, wrap=True)
            if ps_image_id:
                return {'id_default_image': ps_image_id}
