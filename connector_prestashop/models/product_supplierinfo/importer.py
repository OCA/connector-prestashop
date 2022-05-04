# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import FailedJobError

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class SupplierMapper(Component):
    _name = "prestashop.supplier.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.supplier"

    direct = [
        ("name", "name"),
        ("id", "prestashop_id"),
        ("active", "active"),
    ]

    @mapping
    def company_id(self, record):
        return {"company_id": self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def supplier(self, record):
        return {
            "is_company": True,
        }

    @mapping
    def image(self, record):
        supplier_image_adapter = self.component(
            usage="backend.adapter", model_name="prestashop.supplier.image"
        )
        try:
            return {"image": supplier_image_adapter.read(record["id"])}
        except BaseException:
            return {}


class SupplierImporter(Component):
    """Import one simple record"""

    _name = "prestashop.supplier.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.supplier"

    def _create(self, record):
        try:
            return super()._create(record)
        except ZeroDivisionError:
            del record["image"]
            return super()._create(record)


class SupplierBatchImporter(Component):
    _name = "prestashop.supplier.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.supplier"


class SupplierInfoMapper(Component):
    _name = "prestashop.product.supplierinfo.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.product.supplierinfo"

    direct = [
        ("product_supplier_reference", "product_code"),
        ("product_supplier_price_te", "price"),
    ]

    @mapping
    def company_id(self, record):
        return {"company_id": self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def name(self, record):
        binder = self.binder_for("prestashop.supplier")
        partner = binder.to_internal(record["id_supplier"], unwrap=True)
        return {"name": partner.id}

    @mapping
    def product_id(self, record):
        if record["id_product_attribute"] != "0":
            binder = self.binder_for("prestashop.product.combination")
            product = binder.to_internal(
                record["id_product_attribute"],
                unwrap=True,
            )
            return {"product_id": product.id}
        return {}

    @mapping
    def product_tmpl_id(self, record):
        binder = self.binder_for("prestashop.product.template")
        template = binder.to_internal(record["id_product"], unwrap=True)
        return {"product_tmpl_id": template.id}

    @mapping
    def currency_id(self, record):
        binder = self.binder_for("prestashop.res.currency")
        currency = binder.to_internal(record["id_currency"], unwrap=True)
        # Fallback on supplier currency
        if not currency:
            supplier_binder = self.binder_for("prestashop.supplier")
            supplier = supplier_binder.to_internal(record["id_supplier"], unwrap=True)
            currency = supplier.property_purchase_currency_id
        # fallback on company currency
        if not currency:
            currency = self.backend_record.company_id.currency_id
        return {"currency_id": currency.id}

    @mapping
    def required(self, record):
        return {"min_qty": 0.0, "delay": 1}

    @mapping
    def sequence(self, record):
        # In case of variants, we have sometime one supplier info by variant
        # and one dummy supplierinfo with no variant. We put a lower sequence
        # on no variant supplier info so the _select_seller system takes
        # first the one which has variants set
        if record["id_product_attribute"] != "0":
            sequence = 5
        else:
            sequence = 50
        return {"sequence": sequence}


class SupplierInfoImporter(Component):
    _name = "prestashop.product.supplierinfo.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.product.supplierinfo"

    def _import_dependencies(self):
        record = self.prestashop_record
        try:
            self._import_dependency(record["id_supplier"], "prestashop.supplier")
            self._import_dependency(record["id_product"], "prestashop.product.template")

            if record["id_product_attribute"] != "0":
                self._import_dependency(
                    record["id_product_attribute"], "prestashop.product.combination"
                )
        except PrestaShopWebServiceError:
            raise FailedJobError("Error fetching a dependency")


class SupplierInfoBatchImporter(Component):
    _name = "prestashop.product.supplierinfo.batch.importer"
    _inherit = "prestashop.delayed.batch.importer"
    _apply_on = "prestashop.product.supplierinfo"
