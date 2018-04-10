# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class AccountTaxImporter(Component):
    _name = 'prestashop.account.tax.importer'
    _inherit = 'prestashop.auto.matching.importer'
    _apply_on = 'prestashop.account.tax'

#     _model_name = 'prestashop.account.tax'
    _erp_field = 'amount'
    _ps_field = 'rate'

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if self.backend_record.taxes_included and erp_dict['price_include']:
            taxes_inclusion_test = True
        else:
            taxes_inclusion_test = not erp_dict['price_include']
        if not taxes_inclusion_test:
            return False
        return (erp_dict['type_tax_use'] == 'sale' and
                erp_dict['amount_type'] == 'percent' and
                abs(erp_val - float(ps_val)) < 0.01 and
                self.backend_record.company_id.id == erp_dict['company_id'][0])
