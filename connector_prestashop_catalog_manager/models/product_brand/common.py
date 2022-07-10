# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class ProductBrand(models.Model):
    _inherit = "product.brand"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.product.brand",
        inverse_name="odoo_id",
        copy=False,
        string="PrestaShop Product Brand Bindings",
    )


class PrestashopProductBrand(models.Model):
    _name = "prestashop.product.brand"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"product.brand": "odoo_id"}
    _description = "Prestashop Product Brand"

    odoo_id = fields.Many2one(
        comodel_name="product.brand", string="Brand", required=True, ondelete="cascade",
    )


class PrestashopProductBrandModelBinder(Component):
    _name = "prestashop.product.brand.binder"
    _inherit = "prestashop.binder"
    _apply_on = "prestashop.product.brand"


class PrestashopProductBrandListener(Component):
    _name = "prestashop.product.brand.event.listener"
    _inherit = "prestashop.connector.listener"
    _apply_on = "prestashop.product.brand"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        """Called when a record is created"""
        record.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    @skip_if(lambda self, record, **kwargs: self.need_to_export(record, **kwargs))
    def on_record_write(self, record, fields=None):
        """Called when a record is written"""
        record.with_delay().export_record(fields=fields)


class ProductBrandListener(Component):
    _name = "product.brand.event.listener"
    _inherit = "prestashop.connector.listener"
    _apply_on = "product.brand"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """Called when a record is written"""
        for binding in record.prestashop_bind_ids:
            if not self.need_to_export(binding, fields):
                binding.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        """Called when a record is deleted"""
        for binding in record.prestashop_bind_ids:
            work = self.work.work_on(collection=binding.backend_id)
            binder = work.component(
                usage="binder", model_name="prestashop.product.brand"
            )
            prestashop_id = binder.to_external(binding)
            if prestashop_id:
                self.env["prestashop.product.brand"].with_delay().export_delete_record(
                    binding.backend_id, prestashop_id
                )
