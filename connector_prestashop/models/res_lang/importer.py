# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from ...unit.auto_matching_importer import AutoMatchingImporter
from ...backend import prestashop


@prestashop
class LangImporter(AutoMatchingImporter):
    _model_name = 'prestashop.res.lang'
    _erp_field = 'code'
    _ps_field = 'language_code'
    _copy_fields = [
        ('active', 'active'),
    ]

    def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if len(erp_val) >= 2 and len(ps_val) >= 2 and \
                erp_val[0:2].lower() == ps_val[0:2].lower():
            return True
        return False
