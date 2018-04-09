# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from ...components.auto_matching_importer import AutoMatchingImporter
from ...backend import prestashop


@prestashop
class CountryImporter(AutoMatchingImporter):
    _name = 'prestashop.res.country.importer'
    _apply_on = 'prestashop.res.country'

    _erp_field = 'code'
    _ps_field = 'iso_code'

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if (
            erp_val and
            ps_val and
            len(erp_val) >= 2 and
            len(ps_val) >= 2 and
            erp_val[0:2].lower() == ps_val[0:2].lower()
        ):
            return True
        return False
