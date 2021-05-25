# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrestashopExportProductBrand(models.TransientModel):
    _name = "wiz.prestashop.export.product.brand"
    _description = "Prestashop Export Product Brand"

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

    def export_product_brands(self):
        self.ensure_one()
        brand_obj = self.env["product.brand"]
        ps_product_brand_obj = self.env["prestashop.product.brand"]
        for prod_brand in brand_obj.browse(self.env.context["active_ids"]):
            ps_product_brand = ps_product_brand_obj.search(
                [
                    ("odoo_id", "=", prod_brand.id),
                    ("backend_id", "=", self.backend_id.id),
                ]
            )
            if not ps_product_brand:
                ps_product_brand_obj.create(
                    {
                        "backend_id": self.backend_id.id,
                        "odoo_id": prod_brand.id,
                    }
                )
