# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ProductInventoryExporter(Component):
    _name = 'prestashop.product.template.inventory.exporter'
    _inherit = 'prestashop.exporter'
    _apply_on = 'prestashop.product.template'
    _usage = 'inventory.exporter'

    def get_filter(self, template):
        binder = self.binder_for()
        prestashop_id = binder.to_external(template)
        return {
            'filter[id_product]': prestashop_id,
            'filter[id_product_attribute]': 0
        }

    def get_quantity_vals(self, template):
        return {
            'quantity': int(template.quantity),
            'out_of_stock': int(template.out_of_stock),
        }

    def run(self, template, fields):
        """ Export the product inventory to PrestaShop """
        adapter = self.component(
            usage='backend.adapter', model_name='_import_stock_available'
        )
        filter = self.get_filter(template)
        quantity_vals = self.get_quantity_vals(template)
        adapter.export_quantity(filter, quantity_vals)
