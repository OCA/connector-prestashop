# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ResCurrencyImporter(Component):
    _name = "prestashop.res.currency.importer"
    _inherit = "prestashop.auto.matching.importer"
    _apply_on = "prestashop.res.currency"

    _erp_field = "name"
    _ps_field = "iso_code"
    _filters = {"filter[deleted]": "0"}

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if (
            len(erp_val) == 3
            and len(ps_val) == 3
            and erp_val[0:3].lower() == ps_val[0:3].lower()
        ):
            return True
        return False
