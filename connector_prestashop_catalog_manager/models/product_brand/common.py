# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class PrestashopProductBrandListener(Component):
    _name = "prestashop.product.brand.event.listener"
    _inherit = "prestashop.connector.listener"
    _apply_on = "prestashop.product.brand"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        """ Called when a record is created """
        record.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    @skip_if(lambda self, record, **kwargs: self.need_to_export(record, **kwargs))
    def on_record_write(self, record, fields=None):
        """ Called when a record is written """
        record.with_delay().export_record(fields=fields)


class ProductBrandListener(Component):
    _name = "product.brand.event.listener"
    _inherit = "prestashop.connector.listener"
    _apply_on = "product.brand"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """ Called when a record is written """
        for binding in record.prestashop_bind_ids:
            if not self.need_to_export(binding, fields):
                binding.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        """ Called when a record is deleted """
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
