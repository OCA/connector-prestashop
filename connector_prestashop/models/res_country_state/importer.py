# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class CountryImporter(Component):
    _name = "prestashop.res.country.state.importer"
    _inherit = "prestashop.auto.matching.importer"
    _apply_on = "prestashop.res.country.state"

    _erp_field = "code"
    _ps_field = "iso_code"
    _filters = {"filter[active]": "1"}

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        return erp_val.lower() == ps_val.lower()
