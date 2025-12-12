# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class LangImporter(Component):
    _name = "prestashop.res.lang.importer"
    _inherit = "prestashop.auto.matching.importer"
    _apply_on = "prestashop.res.lang"

    _erp_field = "code"
    _ps_field = "language_code"
    _copy_fields = [
        ("active", "active"),
    ]

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if len(erp_val.split("_")) == 2 and len(ps_val.split("-")) == 2:
            ps_val_lang, ps_val_country = ps_val.split("-")
            erp_val_lang, erp_val_country = erp_val.split("_")
            if (
                len(ps_val_lang) == 2
                and len(erp_val_lang) == 2
                and ps_val_lang.lower() == erp_val_lang.lower()
                and len(ps_val_country) == 2
                and len(erp_val_country) == 2
                and ps_val_country.lower() == erp_val_country.lower()
            ):
                return True
        elif (
            len(erp_val) >= 2
            and len(ps_val) >= 2
            and erp_val[0:2].lower() == ps_val[0:2].lower()
        ):
            return True
        return False
