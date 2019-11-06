# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductCombinationExporter(Component):
    _inherit = 'prestashop.product.combination.exporter'

    def _after_export(self):
        super(ProductCombinationExporter, self)._after_export()
        listener = self.component(
            model_name='product.pricelist.item', usage='event.listener')
        for item in self.binding.pricelist_item_ids:
            listener._check_bindings(item)
            for binding in item.prestashop_bind_ids:
                if binding.backend_id.id != self.backend_record.id:
                    continue
                if binding.prestashop_id:
                    continue
                binding.with_delay().export_record()
