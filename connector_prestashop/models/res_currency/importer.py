# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from ...components.auto_matching_importer import AutoMatchingImporter
from ...backend import prestashop


@prestashop
class ResCurrencyImporter(AutoMatchingImporter):
    _name = 'prestashop.res.currency.importer'
    _apply_on = 'prestashop.res.currency'

    _erp_field = 'name'
    _ps_field = 'iso_code'

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if len(erp_val) == 3 and len(ps_val) == 3 and \
                erp_val[0:3].lower() == ps_val[0:3].lower():
            return True
        return False
