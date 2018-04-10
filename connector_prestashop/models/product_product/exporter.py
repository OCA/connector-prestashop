# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from ...backend import prestashop
from ..product_template.exporter import ProductInventoryExporter


# # @prestashop
class CombinationInventoryExporter(ProductInventoryExporter):
    _model_name = ['prestashop.product.combination']

    def get_filter(self, template):
        return {
            'filter[id_product]': template.main_template_id.prestashop_id,
            'filter[id_product_attribute]': template.prestashop_id,
        }
