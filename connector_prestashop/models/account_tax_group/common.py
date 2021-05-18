# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.account.tax.group",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        index=True,
        string="Company",
    )
    tax_ids = fields.One2many(
        comodel_name="account.tax",
        inverse_name="tax_group_id",
        string="Taxes",
    )


class PrestashopAccountTaxGroup(models.Model):
    _name = "prestashop.account.tax.group"
    # Since the prestashop tax group change its ID when updated we could
    # end up with multiple tax group binding with the same backend_id/odoo_id
    # that is why we do not inherit prestashop.odoo.binding
    _inherit = "prestashop.binding"
    _inherits = {"account.tax.group": "odoo_id"}
    _description = "Account Tax Group Prestashop Bindings"

    odoo_id = fields.Many2one(
        comodel_name="account.tax.group",
        string="Tax Group",
        required=True,
        ondelete="cascade",
    )


class TaxGroupAdapter(Component):
    _name = "prestashop.account.tax.group.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.account.tax.group"

    _model_name = "prestashop.account.tax.group"
    _prestashop_model = "tax_rule_groups"

    def search(self, filters=None):
        if filters is None:
            filters = {}
        filters["filter[deleted]"] = 0
        return super().search(filters)
