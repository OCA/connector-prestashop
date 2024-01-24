# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class PrestashopResLang(models.Model):
    _name = "prestashop.res.lang"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"res.lang": "odoo_id"}
    _description = "Shop lang prestashop bindings"

    odoo_id = fields.Many2one(
        comodel_name="res.lang",
        required=True,
        ondelete="cascade",
        string="Language",
    )
    active = fields.Boolean(
        string="Active in PrestaShop",
        default=False,
    )


class ResLang(models.Model):
    _inherit = "res.lang"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.res.lang",
        inverse_name="odoo_id",
        readonly=True,
        string="PrestaShop Bindings",
    )


class ResLangAdapter(Component):
    _name = "prestashop.res.lang.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.res.lang"
    _prestashop_model = "languages"
