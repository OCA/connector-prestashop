# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    external_to_m2o,
    mapping,
    only_create,
)


class PartnerImportMapper(Component):
    _name = "prestashop.res.partner.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.res.partner"

    direct = [
        ("date_add", "date_add"),
        ("date_upd", "date_upd"),
        ("email", "email"),
        ("newsletter", "newsletter"),
        ("company", "company"),
        ("active", "active"),
        ("note", "comment"),
        (external_to_m2o("id_shop_group"), "shop_group_id"),
        (external_to_m2o("id_shop"), "shop_id"),
        (external_to_m2o("id_default_group"), "default_category_id"),
    ]

    @mapping
    def pricelist(self, record):
        binder = self.binder_for("prestashop.groups.pricelist")
        pricelist = binder.to_internal(record["id_default_group"], unwrap=True)
        if not pricelist:
            return {}
        return {"property_product_pricelist": pricelist.id}

    @mapping
    def is_company(self, record):
        if record.get("company"):
            return {"is_company": True}
        return {}

    @mapping
    def birthday(self, record):
        if record["birthday"] in ["0000-00-00", ""]:
            return {}
        return {"birthday": record["birthday"]}

    @mapping
    def name(self, record):
        parts = [record["firstname"], record["lastname"]]
        name = " ".join(p.strip() for p in parts if p.strip())
        return {"name": name}

    @mapping
    def groups(self, record):
        groups = (
            record.get("associations", {})
            .get("groups", {})
            .get(self.backend_record.get_version_ps_key("group"), [])
        )
        if not isinstance(groups, list):
            groups = [groups]
        model_name = "prestashop.res.partner.category"
        partner_category_bindings = self.env[model_name].browse()
        binder = self.binder_for(model_name)
        for group in groups:
            partner_category_bindings |= binder.to_internal(group["id"])

        result = {
            "group_ids": [(6, 0, partner_category_bindings.ids)],
            "category_id": [(4, b.odoo_id.id) for b in partner_category_bindings],
        }
        return result

    @mapping
    def lang(self, record):
        binder = self.binder_for("prestashop.res.lang")
        erp_lang = None
        if record.get("id_lang"):
            erp_lang = binder.to_internal(record["id_lang"])
        if not erp_lang:
            erp_lang = self.env.ref("base.lang_en")
        return {"lang": erp_lang.code}

    @mapping
    def customer(self, record):
        return {"customer": True}

    @mapping
    def company_id(self, record):
        return {"company_id": self.backend_record.company_id.id}


class ResPartnerImporter(Component):
    _name = "prestashop.res.partner.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.res.partner"

    def _import_dependencies(self):
        groups = (
            self.prestashop_record.get("associations", {})
            .get("groups", {})
            .get(self.backend_record.get_version_ps_key("group"), [])
        )
        if not isinstance(groups, list):
            groups = [groups]
        for group in groups:
            self._import_dependency(group["id"], "prestashop.res.partner.category")

    def _after_import(self, binding):
        super(ResPartnerImporter, self)._after_import(binding)
        binder = self.binder_for()
        ps_id = binder.to_external(binding)
        self.env["prestashop.address"].with_delay(priority=10).import_batch(
            backend=self.backend_record,
            filters={"filter[id_customer]": "%d" % (ps_id,)},
        )


class PartnerBatchImporter(Component):
    _name = "prestashop.res.partner.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.res.partner"


class AddressImportMapper(Component):
    _name = "prestashop.address.mappper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.address"

    direct = [
        ("address1", "street"),
        ("address2", "street2"),
        ("city", "city"),
        ("other", "comment"),
        ("phone", "phone"),
        ("phone_mobile", "mobile"),
        ("postcode", "zip"),
        ("date_add", "date_add"),
        ("date_upd", "date_upd"),
        ("alias", "alias"),
        ("company", "company"),
        (external_to_m2o("id_customer"), "prestashop_partner_id"),
    ]

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def parent_id(self, record):
        binder = self.binder_for("prestashop.res.partner")
        parent = binder.to_internal(record["id_customer"], unwrap=True)
        return {"parent_id": parent.id}

    @mapping
    def name(self, record):
        parts = [record["firstname"], record["lastname"]]
        name = " ".join(p.strip() for p in parts if p.strip())
        return {"name": name}

    @mapping
    def customer(self, record):
        return {"customer": True}

    @mapping
    def country(self, record):
        if record.get("id_country"):
            binder = self.binder_for("prestashop.res.country")
            country = binder.to_internal(record["id_country"], unwrap=True)
            return {"country_id": country.id}
        return {}

    @mapping
    def company_id(self, record):
        return {"company_id": self.backend_record.company_id.id}

    @only_create
    @mapping
    def type(self, record):
        # do not set 'contact', otherwise the address fields are shared with
        # the parent
        return {"type": "other"}


class AddressImporter(Component):
    _name = "prestashop.address.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.address"

    def _check_vat(self, vat_number, partner_country):
        vat_country, vat_number_ = self.env["res.partner"]._split_vat(vat_number)
        if not self.env["res.partner"].simple_vat_check(vat_country, vat_number_):
            # if fails, check with country code from country
            country_code = partner_country.code
            if country_code:
                if not self.env["res.partner"].simple_vat_check(
                    country_code.lower(), vat_number
                ):
                    return False
        return True

    def _after_import(self, binding):
        record = self.prestashop_record
        vat_number = None
        if record["vat_number"]:
            vat_number = record["vat_number"].replace(".", "").replace(" ", "")
        # TODO move to custom localization module
        elif not record["vat_number"] and record.get("dni"):
            vat_number = (
                record["dni"].replace(".", "").replace(" ", "").replace("-", "")
            )
        if vat_number:
            if self._check_vat(vat_number, binding.odoo_id.country_id):
                binding.parent_id.write({"vat": vat_number})
            else:
                msg = _("Please, check the VAT number: %s") % vat_number
                self.backend_record.add_checkpoint(
                    binding.parent_id,
                    message=msg,
                )


class AddressBatchImporter(Component):
    _name = "prestashop.address.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.address"
