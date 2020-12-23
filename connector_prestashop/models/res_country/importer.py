# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class CountryImporter(Component):
    _name = "prestashop.res.country.importer"
    _inherit = "prestashop.auto.matching.importer"
    _apply_on = "prestashop.res.country"

    _erp_field = "code"
    _ps_field = "iso_code"

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        # All code in Odoo have 2 char, it seems dangerous to cut the code
        # before comparing and it can leads to error...
        if len(ps_val) != 2:
            return False
        if (
            erp_val
            and ps_val
            and len(erp_val) >= 2
            and len(ps_val) >= 2
            and erp_val[0:2].lower() == ps_val[0:2].lower()
        ):
            return True
        return False
