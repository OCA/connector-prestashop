# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class SaleOrderState(models.Model):
    _name = "sale.order.state"
    _description = "Sale Order States"

    name = fields.Char("Name", translate=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
    )
    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.sale.order.state",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )


class PrestashopSaleOrderState(models.Model):
    _name = "prestashop.sale.order.state"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"sale.order.state": "odoo_id"}
    _description = "Sale order state prestashop bindings"

    openerp_state_ids = fields.One2many(
        comodel_name="sale.order.state.list",
        inverse_name="prestashop_state_id",
        string="Odoo States",
    )
    odoo_id = fields.Many2one(
        comodel_name="sale.order.state",
        required=True,
        ondelete="cascade",
        string="Sale Order State",
    )


class SaleOrderStateList(models.Model):
    _name = "sale.order.state.list"
    _description = "Sale Order State List"

    name = fields.Selection(
        selection=[
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Odoo State",
        required=True,
    )
    prestashop_state_id = fields.Many2one(
        comodel_name="prestashop.sale.order.state",
        string="PrestaShop State",
    )
    prestashop_id = fields.Integer(
        related="prestashop_state_id.prestashop_id",
        readonly=True,
        store=True,
        string="PrestaShop ID",
    )


class SaleOrderStateAdapter(Component):
    _name = "prestashop.sale.order.state.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.sale.order.state"
    _prestashop_model = "order_states"
