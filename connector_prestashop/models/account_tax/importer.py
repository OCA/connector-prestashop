# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from ...backend import prestashop
from ...unit.direct_binder import DirectBinder


@prestashop
class AccountTaxDirectBinder(DirectBinder):
    _model_name = 'prestashop.account.tax'
    _erp_field = 'amount'
    _ps_field = 'rate'

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        taxes_inclusion_test = self.backend_record.taxes_included and \
            erp_dict['price_include'] or not erp_dict['price_include']
        if taxes_inclusion_test and erp_dict['type_tax_use'] == 'sale' and \
                abs(erp_val*100 - float(ps_val)) < 0.01 and \
                self.backend_record.company_id.id == erp_dict['company_id'][0]:
            return True
        return False
