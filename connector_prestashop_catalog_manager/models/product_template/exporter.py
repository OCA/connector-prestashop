# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
import unicodedata
from datetime import timedelta

from odoo import fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import changed_by, m2o_to_external, mapping

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
    uni = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[\W_]", " ", uni).strip().lower()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


class ProductTemplateExporter(Component):
    _name = "prestashop.product.template.exporter"
    _inherit = "translation.prestashop.exporter"
    _apply_on = "prestashop.product.template"

    def _create(self, record):
        res = super()._create(record)
        self.write_binging_vals(self.binding, record)
        return res["prestashop"]["product"]["id"]

    def _update(self, data):
        """ Update an Prestashop record """
        assert self.prestashop_id
        self.check_images()
        self.backend_adapter.write(self.prestashop_id, data)

    def write_binging_vals(self, erp_record, ps_record):
        keys_to_update = [
            ("description_short_html", "description_short"),
            ("description_html", "description"),
        ]
        trans = self.component(usage="record.importer")
        splitted_record = trans._split_per_language(ps_record)
        for lang_code, prestashop_record in list(splitted_record.items()):
            vals = {}
            for key in keys_to_update:
                vals[key[0]] = prestashop_record[key[1]]
            erp_record.with_context(connector_no_export=True, lang=lang_code).write(
                vals
            )

    def export_categories(self, category):
        if not category:
            return
        category_binder = self.binder_for("prestashop.product.category")
        ext_id = category_binder.to_external(category, wrap=True)
        if ext_id:
            return ext_id

        ps_categ_obj = self.env["prestashop.product.category"]
        position_cat_id = ps_categ_obj.search([], order="position desc", limit=1)
        obj_position = position_cat_id.position + 1
        res = {
            "backend_id": self.backend_record.id,
            "odoo_id": category.id,
            "link_rewrite": get_slug(category.name),
            "position": obj_position,
        }
        binding = ps_categ_obj.with_context(connector_no_export=True).create(res)
        binding.export_record()

    def _parent_length(self, categ):
        if not categ.parent_id:
            return 1
        else:
            return 1 + self._parent_length(categ.parent_id)

    def export_brand(self, brand):
        if not brand:
            return
        brand_binder = self.binder_for("prestashop.product.brand")
        ext_id = brand_binder.to_external(brand, wrap=True)
        if ext_id:
            return ext_id

        ps_brand_obj = self.env["prestashop.product.brand"]
        res = {
            "backend_id": self.backend_record.id,
            "odoo_id": brand.id,
            "link_rewrite": get_slug(brand.name),
        }
        binding = ps_brand_obj.with_context(connector_no_export=True).create(res)
        binding.export_record()

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        super()._export_dependencies()
        attribute_binder = self.binder_for("prestashop.product.combination.option")
        option_binder = self.binder_for("prestashop.product.combination.option.value")

        for category in self.binding.categ_ids:
            self.export_categories(category)

        self.export_brand(self.binding.product_brand_id)

        for line in self.binding.attribute_line_ids:
            attribute_ext_id = attribute_binder.to_external(
                line.attribute_id, wrap=True
            )
            if not attribute_ext_id:
                self._export_dependency(
                    line.attribute_id, "prestashop.product.combination.option"
                )
            for value in line.value_ids:
                value_ext_id = option_binder.to_external(value, wrap=True)
                if not value_ext_id:
                    self._export_dependency(
                        value, "prestashop.product.combination.option.value"
                    )

    def export_variants(self):
        combination_obj = self.env["prestashop.product.combination"]
        for product in self.binding.product_variant_ids:
            if not product.product_template_attribute_value_ids:
                continue
            combination_ext = combination_obj.search(
                [
                    ("backend_id", "=", self.backend_record.id),
                    ("odoo_id", "=", product.id),
                ]
            )
            if not combination_ext:
                combination_ext = combination_obj.with_context(
                    connector_no_export=True
                ).create(
                    {
                        "backend_id": self.backend_record.id,
                        "odoo_id": product.id,
                        "main_template_id": self.binding_id,
                    }
                )
            # If a template has been modified then always update PrestaShop
            # combinations
            combination_ext.with_delay(
                priority=50, eta=timedelta(seconds=20)
            ).export_record()

    def _not_in_variant_images(self, image):
        images = []
        if len(self.binding.product_variant_ids) > 1:
            for product in self.binding.product_variant_ids:
                images.extend(product.image_ids.ids)
        return image.id not in images

    def check_images(self):
        if self.binding.image_ids:
            image_binder = self.binder_for("prestashop.product.image")
            for image in self.binding.image_ids:
                image_ext_id = image_binder.to_external(image, wrap=True)
                # `image_ext_id` is ZERO as long as the image is not exported.
                # Here we delay the export so,
                # if we don't check this we create 2 records to be sync'ed
                # and this leads to:
                # ValueError:
                #   Expected singleton: prestashop.product.image(x, y)
                if image_ext_id is None:
                    image_ext = (
                        self.env["prestashop.product.image"]
                        .with_context(connector_no_export=True)
                        .create(
                            {
                                "backend_id": self.backend_record.id,
                                "odoo_id": image.id,
                            }
                        )
                    )
                    image_ext.with_delay(priority=5).export_record()

    def update_quantities(self):
        if len(self.binding.product_variant_ids) == 1:
            product = self.binding.odoo_id.product_variant_ids[0]
            product.update_prestashop_quantities()

    def _after_export(self):
        self.check_images()
        self.export_variants()
        self.update_quantities()
        if not self.binding.date_add:
            self.binding.with_context(
                connector_no_export=True
            ).date_add = fields.Datetime.now()


class ProductTemplateExportMapper(Component):
    _name = "prestashop.product.template.export.mapper"
    _inherit = "translation.prestashop.export.mapper"
    _apply_on = "prestashop.product.template"

    direct = [
        ("available_for_order", "available_for_order"),
        ("show_price", "show_price"),
        ("online_only", "online_only"),
        ("weight", "weight"),
        ("standard_price", "wholesale_price"),
        (m2o_to_external("default_shop_id"), "id_shop_default"),
        ("always_available", "active"),
        ("barcode", "barcode"),
        ("additional_shipping_cost", "additional_shipping_cost"),
        ("minimal_quantity", "minimal_quantity"),
        ("on_sale", "on_sale"),
        ("date_add", "date_add"),
        ("barcode", "ean13"),
        (
            m2o_to_external(
                "prestashop_default_category_id", binding="prestashop.product.category"
            ),
            "id_category_default",
        ),
        ("state", "state"),
        ("low_stock_threshold", "low_stock_threshold"),
        ("default_code", "reference"),
        (
            m2o_to_external("product_brand_id", binding="prestashop.product.brand"),
            "id_manufacturer",
        ),
        ("visibility", "visibility"),
    ]
    # handled by base mapping `translatable_fields`
    _translatable_fields = [
        ("name", "name"),
        ("link_rewrite", "link_rewrite"),
        ("meta_title", "meta_title"),
        ("meta_description", "meta_description"),
        ("meta_keywords", "meta_keywords"),
        ("tags", "tags"),
        ("available_now", "available_now"),
        ("available_later", "available_later"),
        ("description_short_html", "description_short"),
        ("description_html", "description"),
    ]

    def _get_factor_tax(self, tax):
        return (1 + tax.amount / 100) if tax.price_include else 1.0

    @changed_by("taxes_id", "list_price")
    @mapping
    def list_price(self, record):
        tax = record.taxes_id
        pricelist = record.backend_id.pricelist_id
        if pricelist:
            prices = pricelist.get_products_price([record.odoo_id], [1.0], [None])
            price_to_export = prices.get(record.odoo_id.id)
        else:
            price_to_export = record.list_price
        if tax.price_include and tax.amount_type == "percent":
            # 6 is the rounding precision used by PrestaShop for the
            # tax excluded price.  we can get back a 2 digits tax included
            # price from the 6 digits rounded value
            return {"price": str(round(price_to_export / self._get_factor_tax(tax), 6))}
        else:
            return {"price": str(price_to_export)}

    def _get_product_category(self, record):
        ext_categ_ids = []
        binder = self.binder_for("prestashop.product.category")
        for category in record.categ_ids:
            ext_categ_ids.append({"id": binder.to_external(category, wrap=True)})
        return ext_categ_ids

    def _get_product_image(self, record):
        ext_image_ids = []
        binder = self.binder_for("prestashop.product.image")
        for image in record.image_ids:
            ext_image_ids.append({"id": binder.to_external(image, wrap=True)})
        return ext_image_ids

    @changed_by(
        "attribute_line_ids",
        "categ_ids",
        "categ_id",
        "image_ids",
    )
    @mapping
    def associations(self, record):
        return {
            "associations": {
                "categories": {"category_id": self._get_product_category(record)},
                "images": {"image": self._get_product_image(record)},
            }
        }

    @changed_by("taxes_id")
    @mapping
    def tax_ids(self, record):
        if not record.taxes_id:
            return
        binder = self.binder_for("prestashop.account.tax.group")
        ext_id = binder.to_external(record.taxes_id[:1].tax_group_id, wrap=True)
        return {"id_tax_rules_group": ext_id}

    @changed_by("available_date")
    @mapping
    def available_date(self, record):
        if record.available_date:
            return {"available_date": record.available_date.strftime("%Y-%m-%d")}
        return {}

    @mapping
    def date_add(self, record):
        # When export a record the date_add in PS is null.
        return {"date_add": record.create_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}

    @mapping
    def default_image(self, record):
        default_image = record.image_ids.filtered("front_image")[:1]
        if default_image:
            binder = self.binder_for("prestashop.product.image")
            ps_image_id = binder.to_external(default_image, wrap=True)
            if ps_image_id:
                return {"id_default_image": ps_image_id}

    @mapping
    def low_stock_alert(self, record):
        return {"low_stock_alert": "1" if record.low_stock_alert else "0"}
