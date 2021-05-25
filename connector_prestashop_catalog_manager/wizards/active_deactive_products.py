# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SyncProducts(models.TransientModel):
    _name = "active.deactive.products"
    _description = "Activate/Deactivate Products"

    force_status = fields.Boolean(
        string="Force Status",
        help="Check this option to force active product in prestashop",
    )

    def _change_status(self, status):
        self.ensure_one()
        product_obj = self.env["product.template"]
        for product in product_obj.browse(self.env.context["active_ids"]):
            for bind in product.prestashop_bind_ids:
                if bind.always_available != status or self.force_status:
                    bind.always_available = status

    def active_products(self):
        for product in self:
            product._change_status(True)

    def deactive_products(self):
        for product in self:
            product._change_status(False)
