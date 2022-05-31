# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import models

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class ProductCombinationImporter(Component):
    _name = "prestashop.product.combination.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.product.combination"

    #    def _import_dependencies(self):
    #        record = self.prestashop_record
    #        ps_key = self.backend_record.get_version_ps_key("product_option_value")
    #        option_values = (
    #            record.get("associations", {})
    #            .get("product_option_values", {})
    #            .get(ps_key, [])
    #        )
    #        if not isinstance(option_values, list):
    #            option_values = [option_values]
    #        backend_adapter = self.component(
    #            usage="backend.adapter",
    #            model_name="prestashop.product.combination.option.value",
    #        )
    #        presta_option_values = []
    #        for option_value in option_values:
    #            option_value = backend_adapter.read(option_value["id"])
    #            self._import_dependency(
    #                option_value["id_attribute_group"],
    #                "prestashop.product.combination.option",
    #            )
    #            self._import_dependency(
    #                option_value["id"], "prestashop.product.combination.option.value"
    #            )
    #            presta_option_values.append(option_value)
    #        self.template_attribute_lines(presta_option_values)

    def template_attribute_lines(self, option_values):
        record = self.prestashop_record
        template_binder = self.binder_for("prestashop.product.template")
        template = template_binder.to_internal(record["id_product"]).odoo_id
        attribute_values = {}
        option_value_binder = self.binder_for(
            "prestashop.product.combination.option.value"
        )
        option_binder = self.binder_for("prestashop.product.combination.option")
        for option_value in option_values:
            attr_id = option_binder.to_internal(
                option_value["id_attribute_group"]
            ).odoo_id.id
            value_id = option_value_binder.to_internal(option_value["id"]).odoo_id.id
            if attr_id not in attribute_values:
                attribute_values[attr_id] = []
            attribute_values[attr_id].append(value_id)
        for attr_id, value_ids in attribute_values.items():
            attr_line = template.attribute_line_ids.filtered(
                lambda l: l.attribute_id.id == attr_id
            )
            if attr_line:
                attr_line.write({"value_ids": [(6, 0, value_ids)]})
            else:
                attr_line = self.env["product.template.attribute.line"].create(
                    {
                        "attribute_id": attr_id,
                        "product_tmpl_id": template.id,
                        "value_ids": [(6, 0, value_ids)],
                    }
                )
            attr_line._update_product_template_attribute_values()

    def _after_import(self, binding):
        super()._after_import(binding)
        self.import_supplierinfo(binding)

    def set_variant_images(self, combinations):
        backend_adapter = self.component(
            usage="backend.adapter", model_name="prestashop.product.combination"
        )
        for combination in combinations:
            record = backend_adapter.read(combination["id"])
            associations = record.get("associations", {})
            try:
                ps_images = associations.get("images", {}).get(
                    self.backend_record.get_version_ps_key("image"), {}
                )
            except PrestaShopWebServiceError:
                # TODO: don't we track anything here? Maybe a checkpoint?
                continue
            binder = self.binder_for("prestashop.product.image")
            if not isinstance(ps_images, list):
                ps_images = [ps_images]
            if "id" in ps_images[0]:
                images = [
                    binder.to_internal(x.get("id"), unwrap=True) for x in ps_images
                ]
            else:
                continue
            product_binder = self.binder_for("prestashop.product.combination")
            product = product_binder.to_internal(combination["id"], unwrap=True)
            product.with_context(connector_no_export=True).write(
                {"image_ids": [(6, 0, [x.id for x in images])]}
            )

    def import_supplierinfo(self, binding):
        ps_id = self._get_prestashop_data()["id"]
        filters = {
            # 'filter[id_product]': ps_id,
            "filter[id_product_attribute]": ps_id
        }
        self.env["prestashop.product.supplierinfo"].with_delay().import_batch(
            self.backend_record, filters=filters
        )

    def _import(self, binding, **kwargs):
        # We need to pass the template presta record because we need it
        # for combination mapper
        if not hasattr(self.work, "parent_presta_record"):
            tmpl_adapter = self.component(
                usage="backend.adapter", model_name="prestashop.product.template"
            )
            tmpl_record = tmpl_adapter.read(self.prestashop_record.get("id_product"))
            self.work.parent_presta_record = tmpl_record
            if "parent_presta_record" not in self.work._propagate_kwargs:
                self.work._propagate_kwargs.append("parent_presta_record")
        return super()._import(binding, **kwargs)


class ProductCombinationMapper(Component):
    _name = "prestashop.product.combination.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.product.combination"

    direct = []

    from_main = []

    @mapping
    def weight(self, record):
        prestashop_product_tmpl_obj = self.env["prestashop.product.template"]
        combination_weight = float(record.get("weight", "0.0"))
        if not hasattr(self.work, "parent_presta_record"):
            presta_product_tmpl = prestashop_product_tmpl_obj.search(
                [("prestashop_id", "=", record["id_product"])]
            )
            main_weight = presta_product_tmpl.weight
        else:
            main_weight = float(self.work.parent_presta_record.get("weight", 0.0))
        weight = main_weight + combination_weight
        return {"weight": weight}

    @mapping
    def combination_default(self, record):
        return {"default_on": bool(int(record["default_on"] or 0))}

    @only_create
    @mapping
    def product_tmpl_id(self, record):
        template = self.get_main_template_binding(record)
        product_binder = self.binder_for("prestashop.product.combination")
        product = product_binder.to_internal(record["id"])
        if not product or product.product_tmpl_id.id != template.odoo_id.id:
            return {"product_tmpl_id": template.odoo_id.id}
        return {}

    @mapping
    def from_main_template(self, record):
        main_template = self.get_main_template_binding(record)
        result = {}
        for attribute in self.from_main:
            if attribute not in main_template:
                continue
            if hasattr(main_template[attribute], "id"):
                result[attribute] = main_template[attribute].id
            elif type(main_template[attribute]) is models.BaseModel:
                ids = []
                for element in main_template[attribute]:
                    ids.append(element.id)
                result[attribute] = [(6, 0, ids)]
            else:
                result[attribute] = main_template[attribute]
        return result

    def get_main_template_binding(self, record):
        template_binder = self.binder_for("prestashop.product.template")
        return template_binder.to_internal(record["id_product"])

    def _get_option_value(self, record):
        option_values = (
            record.get("associations", {})
            .get("product_option_values", {})
            .get(self.backend_record.get_version_ps_key("product_option_value"), [])
        )
        template_binding = self.get_main_template_binding(record)
        template = template_binding.odoo_id
        if type(option_values) is dict:
            option_values = [option_values]
        tmpl_values = template.attribute_line_ids.mapped("product_template_value_ids")
        for option_value in option_values:
            option_value_binder = self.binder_for(
                "prestashop.product.combination.option.value"
            )
            option_value_binding = option_value_binder.to_internal(option_value["id"])
            tmpl_value = tmpl_values.filtered(
                lambda v: v.product_attribute_value_id.id
                == option_value_binding.odoo_id.id
            )
            assert option_value_binding, "must have a binding for the option"
            yield tmpl_value

    @mapping
    def product_template_attribute_value_ids(self, record):
        results = []
        for tmpl_attr_value in self._get_option_value(record):
            results.append(tmpl_attr_value.id)
        return {"product_template_attribute_value_ids": [(6, 0, results)]}

    @mapping
    def main_template_id(self, record):
        template_binding = self.get_main_template_binding(record)
        return {"main_template_id": template_binding.id}

    def _product_code_exists(self, code):
        model = self.env["product.product"]
        combination_binder = self.binder_for("prestashop.product.combination")
        product = model.with_context(active_test=False).search(
            [
                ("default_code", "=", code),
                ("company_id", "=", self.backend_record.company_id.id),
            ],
            limit=1,
        )
        return product and not combination_binder.to_external(product, wrap=True)

    @mapping
    def default_code(self, record):
        code = record.get("reference")
        if not code:
            code = "{}_{}".format(record["id_product"], record["id"])
        if (
            not self._product_code_exists(code)
            or self.backend_record.matching_product_ch == "reference"
        ):
            return {"default_code": code}
        i = 1
        current_code = "{}_{}".format(code, i)
        while self._product_code_exists(current_code):
            i += 1
            current_code = "{}_{}".format(code, i)
        return {"default_code": current_code}

    #     @mapping
    #     def backend_id(self, record):
    #         return {'backend_id': self.backend_record.id}

    @mapping
    def barcode(self, record):
        barcode = record.get("barcode") or record.get("ean13")
        check_ean = self.env["barcode.nomenclature"].check_ean
        if barcode in ["", "0"]:
            backend_adapter = self.component(
                usage="backend.adapter", model_name="prestashop.product.template"
            )
            template = backend_adapter.read(record["id_product"])
            barcode = template.get("barcode") or template.get("ean13")
        if barcode and barcode != "0" and check_ean(barcode):
            return {"barcode": barcode}
        return {}

    def _get_tax_ids(self, record):
        product_tmpl_adapter = self.component(
            usage="backend.adapter", model_name="prestashop.product.template"
        )
        tax_group = product_tmpl_adapter.read(record["id_product"])
        tax_group = self.binder_for("prestashop.account.tax.group").to_internal(
            tax_group["id_tax_rules_group"], unwrap=True
        )
        return tax_group.tax_ids

    def _apply_taxes(self, tax, price):
        if self.backend_record.taxes_included == tax.price_include:
            return price
        factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
        if self.backend_record.taxes_included:
            if not tax.price_include:
                return price / factor_tax
        else:
            if tax.price_include:
                return price * factor_tax

    @mapping
    def specific_price(self, record):
        product = self.binder_for("prestashop.product.combination").to_internal(
            record["id"], unwrap=True
        )
        product_template = self.binder_for("prestashop.product.template").to_internal(
            record["id_product"]
        )
        tax = product.product_tmpl_id.taxes_id[:1] or self._get_tax_ids(record)
        impact = float(self._apply_taxes(tax, float(record["price"] or "0.0")))
        cost_price = float(record["wholesale_price"] or "0.0")
        return {
            "list_price": product_template.list_price,
            "standard_price": cost_price or product_template.wholesale_price,
            "impact_price": impact,
        }

    @only_create
    @mapping
    def odoo_id(self, record):
        """Will bind the product to an existing one with the same code"""
        if self.backend_record.matching_product_template:
            code = record.get(self.backend_record.matching_product_ch)
            if self.backend_record.matching_product_ch == "reference":
                if code:
                    product = self.env["product.product"].search(
                        [("default_code", "=", code)], limit=1
                    )
                    if product:
                        return {"odoo_id": product.id}
            if self.backend_record.matching_product_ch == "barcode":
                if code:
                    product = self.env["product.product"].search(
                        [("barcode", "=", code)], limit=1
                    )
                    if product:
                        return {"odoo_id": product.id}

        template = self.get_main_template_binding(record).odoo_id
        # if variant already exists linked it since we can't have 2 variants with
        # the exact same attributes

        ps_key = self.backend_record.get_version_ps_key("product_option_value")
        option_values = (
            record.get("associations", {})
            .get("product_option_values", {})
            .get(ps_key, [])
        )
        if not isinstance(option_values, list):
            option_values = [option_values]
        option_value_binder = self.binder_for(
            "prestashop.product.combination.option.value"
        )
        value_ids = [
            option_value_binder.to_internal(option_value["id"]).odoo_id.id
            for option_value in option_values
        ]
        for variant in template.product_variant_ids:
            if sorted(
                variant.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id"
                ).ids
            ) == sorted(value_ids):
                return {"odoo_id": variant.id}
        return {}


class ProductCombinationOptionImporter(Component):
    _name = "prestashop.product.combination.option.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.product.combination.option"

    def _import_values(self, attribute_binding):
        record = self.prestashop_record
        option_values = (
            record.get("associations", {})
            .get("product_option_values", {})
            .get(self.backend_record.get_version_ps_key("product_option_value"), [])
        )
        if not isinstance(option_values, list):
            option_values = [option_values]
        for option_value in option_values:
            self._import_dependency(
                option_value["id"], "prestashop.product.combination.option.value"
            )

    def _after_import(self, binding):
        super()._after_import(binding)
        self._import_values(binding)


class ProductCombinationOptionMapper(Component):
    _name = "prestashop.product.combination.option.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.product.combination.option"

    direct = []

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @only_create
    @mapping
    def odoo_id(self, record):
        name = self.name(record).get("name")
        binding = self.env["product.attribute"].search(
            [("name", "=", name)],
            limit=1,
        )
        if binding:
            return {"odoo_id": binding.id}

    @mapping
    def name(self, record):
        name = None
        if "language" in record["name"]:
            language_binder = self.binder_for("prestashop.res.lang")
            languages = record["name"]["language"]
            if not isinstance(languages, list):
                languages = [languages]
            for lang in languages:
                erp_language = language_binder.to_internal(lang["attrs"]["id"])
                if not erp_language:
                    continue
                if erp_language.code == "en_US":
                    name = lang["value"]
                    break
            if name is None:
                name = languages[0]["value"]
        else:
            name = record["name"]
        return {"name": name}

    @mapping
    def create_variant(self, record):
        # seems the best way. If we do it in automatic, we could have too much variants
        # compared to prestashop if we got more thant 1 attributes, which seems
        # totally possible. If we put no variant, and we delete one value on prestashop
        # product won't be inative by odoo
        # with dynamic, prestashop create it on product import, odoo inactive it if
        # deleted on prestashop...
        # We avoid "You cannot change the Variants Creation Mode of the attribute"
        # error by not changing the attribute when there is existing record
        odoo_id = self.odoo_id(record)
        if not odoo_id:
            return {"create_variant": "dynamic"}


class ProductCombinationOptionValueAdapter(Component):
    _name = "prestashop.product.combination.option.value.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.product.combination.option.value"

    _prestashop_model = "product_option_values"
    _export_node_name = "product_option_value"


class ProductCombinationOptionValueImporter(Component):
    _name = "prestashop.product.combination.option.value.importer"
    _inherit = "prestashop.translatable.record.importer"
    _apply_on = "prestashop.product.combination.option.value"

    _translatable_fields = {
        "prestashop.product.combination.option.value": ["name"],
    }


class ProductCombinationOptionValueMapper(Component):
    _name = "prestashop.product.combination.option.value.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.product.combination.option.value"

    direct = [
        ("name", "name"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        attribute_binder = self.binder_for("prestashop.product.combination.option")
        attribute = attribute_binder.to_internal(
            record["id_attribute_group"], unwrap=True
        )
        assert attribute
        binding = self.env["product.attribute.value"].search(
            [("name", "=", record["name"]), ("attribute_id", "=", attribute.id)],
            limit=1,
        )
        if binding:
            return {"odoo_id": binding.id}

    @mapping
    def attribute_id(self, record):
        binder = self.binder_for("prestashop.product.combination.option")
        attribute = binder.to_internal(record["id_attribute_group"], unwrap=True)
        return {"attribute_id": attribute.id}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}


class ProductProductBatchImporter(Component):
    _name = "prestashop.product.combination.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.product.combination"
