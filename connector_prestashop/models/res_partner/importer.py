# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    external_to_m2o,
    mapping,
    only_create,
)

_logger = logging.getLogger(__name__)


class PartnerImportMapper(Component):
    _name = "prestashop.res.partner.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.res.partner"

    direct = [
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
    def date_add(self, record):
        if record["date_add"] == "0000-00-00 00:00:00":
            return {"date_add": datetime.datetime.now()}
        return {"date_add": record["date_add"]}

    @mapping
    def date_upd(self, record):
        if record["date_upd"] == "0000-00-00 00:00:00":
            return {"date_upd": datetime.datetime.now()}
        return {"date_upd": record["date_upd"]}

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
            partner_category_bindings |= binder.to_internal(group["id"], unwrap=True)

        result = {
            "group_ids": [(6, 0, partner_category_bindings.ids)],
            "category_id": [(4, b.odoo_id.id) for b in partner_category_bindings],
        }
        return result

    @mapping
    def lang(self, record):
        binder = self.binder_for("prestashop.res.lang")
        erp_lang = None
        # We can't put unactive lang so ensure it is active.
        # if not lang, take the one on company
        if record.get("id_lang"):
            erp_lang = binder.to_internal(record["id_lang"], unwrap=True)
            erp_lang = erp_lang.filtered("active")
            lang = erp_lang.code
        if not erp_lang:
            lang = self.env.company.partner_id.lang
        return {"lang": lang}

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
        default_group = self.prestashop_record.get("id_default_group", False)
        if default_group:
            groups.append({"id": default_group})
        for group in groups:
            self._import_dependency(group["id"], "prestashop.res.partner.category")

    def _after_import(self, binding):
        res = super()._after_import(binding)
        binder = self.binder_for()
        ps_id = binder.to_external(binding)
        self.env["prestashop.address"].with_delay(priority=25).import_batch(
            backend=self.backend_record,
            filters={"filter[id_customer]": "%d" % (ps_id,)},
        )
        return res


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
        ("alias", "alias"),
        ("company", "company"),
        (external_to_m2o("id_customer"), "prestashop_partner_id"),
    ]

    @mapping
    def date_add(self, record):
        if record["date_add"] == "0000-00-00 00:00:00":
            return {"date_add": datetime.datetime.now()}
        return {"date_add": record["date_add"]}

    @mapping
    def date_upd(self, record):
        if record["date_upd"] == "0000-00-00 00:00:00":
            return {"date_upd": datetime.datetime.now()}
        return {"date_upd": record["date_upd"]}

    @mapping
    def country_id(self, record):
        binder = self.binder_for("prestashop.res.country")
        country_id = binder.to_internal(record["id_country"], unwrap=True)
        return {"country_id": country_id.id}

    @mapping
    def state_id(self, record):
        binder = self.binder_for("prestashop.res.country.state")
        state_id = binder.to_internal(record["id_state"], unwrap=True)
        return {"state_id": state_id.id}

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
    def company_id(self, record):
        return {"company_id": self.backend_record.company_id.id}

    @only_create
    @mapping
    def type(self, record):
        # do not set 'contact', otherwise the address fields are shared with
        # the parent
        return {"type": record.get("address_type", "other")}


class AddressImporter(Component):
    _name = "prestashop.address.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.address"

    def run(self, prestashop_id, **kwargs):
        if "address_type" in kwargs:
            self._address_type = kwargs.pop("address_type")
        # else: let mapper to set default value
        return super().run(prestashop_id, **kwargs)

    def _map_data(self):
        map_record = super()._map_data()
        try:
            map_record.source["address_type"] = self._address_type
        except AttributeError:  # pragma: no cover
            _logger.info("Mapper can set the default values")
            pass  # let mapper to set default value
        return map_record

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
            binding.parent_id.write({"vat": vat_number})


class AddressBatchImporter(Component):
    _name = "prestashop.address.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.address"
