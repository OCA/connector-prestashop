# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class ProductImage(models.Model):
    _inherit = "base_multi_image.image"

    front_image = fields.Boolean(string="Front image")


class PrestashopProductImageListener(Component):
    _name = "prestashop.product.image.event.listener"
    _inherit = "base.connector.listener"
    _apply_on = "base_multi_image.image"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """ Called when a record is written """
        for binding in record.prestashop_bind_ids:
            binding.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        """ Called when a record is deleted """
        for binding in record.prestashop_bind_ids:
            product = self.env[record.owner_model].browse(record.owner_id)
            if product.exists():
                template = product.prestashop_bind_ids.filtered(
                    lambda x: x.backend_id == binding.backend_id
                )
                if not template:
                    return

                work = self.work.work_on(collection=binding.backend_id)
                binder = work.component(
                    usage="binder", model_name="prestashop.product.image"
                )
                prestashop_id = binder.to_external(binding)
                attributes = {
                    "id_product": template.prestashop_id,
                }
                if prestashop_id:
                    self.env[
                        "prestashop.product.image"
                    ].with_delay().export_delete_record(
                        binding.backend_id, prestashop_id, attributes
                    )
