# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..models.product_template.exporter import get_slug


class PrestashopExportCategory(models.TransientModel):
    _name = "wiz.prestashop.export.category"
    _description = "Prestashop Export Category"

    def _default_backend(self):
        return self.env["prestashop.backend"].search([], limit=1).id

    def _default_shop(self):
        return self.env["prestashop.shop"].search([], limit=1).id

    backend_id = fields.Many2one(
        comodel_name="prestashop.backend",
        default=_default_backend,
        string="Backend",
    )
    shop_id = fields.Many2one(
        comodel_name="prestashop.shop",
        default=_default_shop,
        string="Shop",
    )

    def export_categories(self):
        self.ensure_one()
        category_obj = self.env["product.category"]
        ps_category_obj = self.env["prestashop.product.category"]
        for category in category_obj.browse(self.env.context["active_ids"]):
            ps_category = ps_category_obj.search(
                [
                    ("odoo_id", "=", category.id),
                    ("backend_id", "=", self.backend_id.id),
                    ("default_shop_id", "=", self.shop_id.id),
                ]
            )
            if not ps_category:
                ps_category_obj.create(
                    {
                        "backend_id": self.backend_id.id,
                        "default_shop_id": self.shop_id.id,
                        "link_rewrite": get_slug(category.name),
                        "odoo_id": category.id,
                    }
                )
