# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import fields, models

from odoo.addons.component.core import Component


class PrestashopResCountryState(models.Model):
    _name = "prestashop.res.country.state"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"res.country.state": "odoo_id"}
    _description = "Country state prestashop bindings"

    odoo_id = fields.Many2one(
        comodel_name="res.country.state",
        required=True,
        ondelete="cascade",
        string="State",
    )


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.res.country.state",
        inverse_name="odoo_id",
        readonly=True,
        string="prestashop Bindings",
    )


class ResCountryAdapter(Component):
    _name = "prestashop.res.country.state.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.res.country.state"
    _prestashop_model = "states"
