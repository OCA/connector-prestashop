# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import changed_by, mapping

_logger = logging.getLogger(__name__)


class ProductCombinationExporter(Component):
    _name = "prestashop.product.combination.exporter"
    _inherit = "translation.prestashop.exporter"
    _apply_on = "prestashop.product.combination"

    def _create(self, record):
        """
        :param record: browse record to create in prestashop
        :return integer: Prestashop record id
        """
        res = super()._create(record)
        return res["prestashop"]["combination"]["id"]

    def _export_images(self):
        if self.binding.image_ids:
            image_binder = self.binder_for("prestashop.product.image")
            for image_line in self.binding.image_ids:
                image_ext_id = image_binder.to_external(image_line.id, wrap=True)
                if not image_ext_id:
                    image_ext = (
                        self.env["prestashop.product.image"]
                        .with_context(connector_no_export=True)
                        .create(
                            {
                                "backend_id": self.backend_record.id,
                                "odoo_id": image_line.id,
                            }
                        )
                        .id
                    )
                    image_content = getattr(
                        image_line, "_get_image_from_%s" % image_line.storage
                    )()
                    image_ext.export_record(image_content)

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        # TODO add export of category
        attribute_binder = self.binder_for("prestashop.product.combination.option")
        option_binder = self.binder_for("prestashop.product.combination.option.value")
        Option = self.env["prestashop.product.combination.option"]
        OptionValue = self.env["prestashop.product.combination.option.value"]
        for value in self.binding.product_template_attribute_value_ids:
            prestashop_option_id = attribute_binder.to_external(
                value.attribute_id.id, wrap=True
            )
            if not prestashop_option_id:
                option_binding = Option.search(
                    [
                        ("backend_id", "=", self.backend_record.id),
                        ("odoo_id", "=", value.attribute_id.id),
                    ]
                )
                if not option_binding:
                    option_binding = Option.with_context(
                        connector_no_export=True
                    ).create(
                        {
                            "backend_id": self.backend_record.id,
                            "odoo_id": value.attribute_id.id,
                        }
                    )
                option_binding.export_record()
            prestashop_value_id = option_binder.to_external(
                value.product_attribute_value_id.id, wrap=True
            )
            if not prestashop_value_id:
                value_binding = OptionValue.search(
                    [
                        ("backend_id", "=", self.backend_record.id),
                        ("odoo_id", "=", value.id),
                    ]
                )
                if not value_binding:
                    option_binding = Option.search(
                        [
                            ("backend_id", "=", self.backend_record.id),
                            ("odoo_id", "=", value.attribute_id.id),
                        ]
                    )
                    value_binding = OptionValue.with_context(
                        connector_no_export=True
                    ).create(
                        {
                            "backend_id": self.backend_record.id,
                            "odoo_id": value.product_attribute_value_id.id,
                            "id_attribute_group": option_binding.id,
                        }
                    )
                value_binding.export_record()
        # self._export_images()

    def update_quantities(self):
        self.binding.odoo_id.with_context(self.env.context).update_prestashop_qty()

    def _after_export(self):
        self.update_quantities()


class ProductCombinationExportMapper(Component):
    _name = "prestashop.product.combination.export.mapper"
    _inherit = "translation.prestashop.export.mapper"
    _apply_on = "prestashop.product.combination"

    direct = [
        ("default_code", "reference"),
        ("active", "active"),
        ("barcode", "ean13"),
        ("minimal_quantity", "minimal_quantity"),
        ("weight", "weight"),
    ]

    def _get_factor_tax(self, tax):
        factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
        return factor_tax

    @mapping
    def combination_default(self, record):
        return {"default_on": int(record["default_on"])}

    def get_main_template_id(self, record):
        template_binder = self.binder_for("prestashop.product.template")
        return template_binder.to_external(record.main_template_id.id)

    @mapping
    def main_template_id(self, record):
        return {"id_product": self.get_main_template_id(record)}

    @changed_by("impact_price")
    @mapping
    def _unit_price_impact(self, record):
        pricelist = record.backend_id.pricelist_id
        if pricelist:
            tmpl_prices = pricelist.get_products_price(
                [record.odoo_id.product_tmpl_id], [1.0], [None]
            )
            tmpl_price = tmpl_prices.get(record.odoo_id.product_tmpl_id.id)
            product_prices = pricelist.get_products_price(
                [record.odoo_id], [1.0], [None]
            )
            product_price = product_prices.get(record.odoo_id.id)
            extra_to_export = product_price - tmpl_price
        else:
            extra_to_export = record.impact_price
        tax = record.taxes_id[:1]
        if tax.price_include and tax.amount_type == "percent":
            # 6 is the rounding precision used by PrestaShop for the
            # tax excluded price.  we can get back a 2 digits tax included
            # price from the 6 digits rounded value
            return {"price": round(extra_to_export / self._get_factor_tax(tax), 6)}
        else:
            return {"price": extra_to_export}

    @changed_by("standard_price")
    @mapping
    def cost_price(self, record):
        wholesale_price = float("{:.2f}".format(record.standard_price))
        return {"wholesale_price": wholesale_price}

    def _get_product_option_value(self, record):
        option_value = []
        option_binder = self.binder_for("prestashop.product.combination.option.value")
        for value in record.product_template_attribute_value_ids:
            value_ext_id = option_binder.to_external(
                value.product_attribute_value_id.id, wrap=True
            )
            if value_ext_id:
                option_value.append({"id": value_ext_id})
        return option_value

    def _get_combination_image(self, record):
        images = []
        image_binder = self.binder_for("prestashop.product.image")
        for image in record.image_ids:
            image_ext_id = image_binder.to_external(image.id, wrap=True)
            if image_ext_id:
                images.append({"id": image_ext_id})
        return images

    @changed_by("product_template_attribute_value_ids", "image_ids")
    @mapping
    def associations(self, record):
        return {
            "associations": {
                "product_option_values": {
                    "product_option_value": self._get_product_option_value(record)
                },
                "images": {"image": self._get_combination_image(record)},
            }
        }

    @mapping
    def low_stock_alert(self, record):
        low_stock_alert = False
        if record.product_tmpl_id.prestashop_bind_ids:
            for presta_prod_tmpl in record.product_tmpl_id.prestashop_bind_ids:
                if presta_prod_tmpl.low_stock_alert:
                    low_stock_alert = True
                    break
        return {"low_stock_alert": "1" if low_stock_alert else "0"}


class ProductCombinationOptionExporter(Component):
    _name = "prestashop.product.combination.option.exporter"
    _inherit = "prestashop.exporter"
    _apply_on = "prestashop.product.combination.option"

    def _create(self, record):
        res = super()._create(record)
        return res["prestashop"]["product_option"]["id"]


class ProductCombinationOptionExportMapper(Component):
    _name = "prestashop.product.combination.option.export.mapper"
    _inherit = "translation.prestashop.export.mapper"
    _apply_on = "prestashop.product.combination.option"

    direct = [
        ("prestashop_position", "position"),
        ("display_type", "group_type"),
    ]

    _translatable_fields = [
        ("name", "name"),
        ("name", "public_name"),
    ]


class ProductCombinationOptionValueExporter(Component):
    _name = "prestashop.product.combination.option.value.exporter"
    _inherit = "prestashop.exporter"
    _apply_on = "prestashop.product.combination.option.value"

    def _create(self, record):
        res = super()._create(record)
        return res["prestashop"]["product_option_value"]["id"]

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        attribute_id = self.binding.attribute_id.id
        # export product attribute
        attr_model = "prestashop.product.combination.option"
        binder = self.binder_for(attr_model)
        if not binder.to_external(attribute_id, wrap=True):
            with self.backend_id.work_on(attr_model) as work:
                exporter = work.component(usage="record.exporter")
                exporter.run(attribute_id)
        return


class ProductCombinationOptionValueExportMapper(Component):
    _name = "prestashop.product.combination.option.value.export.mapper"
    _inherit = "translation.prestashop.export.mapper"
    _apply_on = "prestashop.product.combination.option.value"

    direct = [
        ("name", "value"),
        ("prestashop_position", "position"),
    ]
    # handled by base mapping `translatable_fields`
    _translatable_fields = [
        ("name", "name"),
    ]

    @mapping
    def prestashop_product_attribute_id(self, record):
        attribute_binder = self.binder_for(
            "prestashop.product.combination.option.value"
        )
        return {
            "id_feature": attribute_binder.to_external(
                record.attribute_id.id, wrap=True
            )
        }

    @mapping
    def prestashop_product_group_attribute_id(self, record):
        attribute_binder = self.binder_for("prestashop.product.combination.option")
        return {
            "id_attribute_group": attribute_binder.to_external(
                record.attribute_id.id, wrap=True
            ),
        }
