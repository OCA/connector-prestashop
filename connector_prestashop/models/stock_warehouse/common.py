# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models

from odoo.addons.component.core import Component


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.shop",
        inverse_name="odoo_id",
        readonly=True,
        string="PrestaShop Bindings",
    )


class PrestashopShop(models.Model):
    _name = "prestashop.shop"
    _inherit = "prestashop.binding"
    _description = "PrestaShop Shop"

    @api.depends("shop_group_id", "shop_group_id.backend_id")
    def _compute_backend_id(self):
        for shop in self:
            shop.backend_id = shop.shop_group_id.backend_id.id

    name = fields.Char(
        string="Name", help="The name of the method on the backend", required=True
    )
    shop_group_id = fields.Many2one(
        comodel_name="prestashop.shop.group",
        string="PrestaShop Shop Group",
        required=True,
        ondelete="cascade",
    )
    odoo_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="WareHouse",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    backend_id = fields.Many2one(
        compute="_compute_backend_id",
        comodel_name="prestashop.backend",
        string="PrestaShop Backend",
        store=True,
    )
    default_url = fields.Char("Default url")


class ShopAdapter(Component):
    _name = "prestashop.shop"
    _model_name = "prestashop.shop"
    _inherit = "prestashop.adapter"
    _prestashop_model = "shops"
    _apply_on = "prestashop.shop"
