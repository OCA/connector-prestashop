# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class PrestashopAccountTax(models.Model):
    _name = "prestashop.account.tax"
    # Do not inherit from `prestashop.binding.odoo`
    # because we do not want the constraint `prestashop_erp_uniq`.
    # This allows us to create duplicated taxes.
    _inherit = "prestashop.binding"
    _inherits = {"account.tax": "odoo_id"}

    odoo_id = fields.Many2one(
        comodel_name="account.tax",
        string="Tax",
        required=True,
        ondelete="cascade",
        oldname="openerp_id",
    )


class AccountTax(models.Model):
    _inherit = "account.tax"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.account.tax",
        inverse_name="odoo_id",
        string="prestashop Bindings",
        readonly=True,
    )


class AccountTaxAdapter(Component):
    _name = "prestashop.account.tax.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.account.tax"

    _model_name = "prestashop.account.tax"
    _prestashop_model = "taxes"
