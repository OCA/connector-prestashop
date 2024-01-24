# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class CombinationInventoryExporter(Component):
    _name = "prestashop.product.combination.inventory.exporter"
    _inherit = "prestashop.product.template.inventory.exporter"
    _apply_on = "prestashop.product.combination"

    def get_filter(self, product):
        return {
            "filter[id_product]": product.main_template_id.prestashop_id,
            "filter[id_product_attribute]": product.prestashop_id,
        }

    def get_quantity_vals(self, product):
        vals = {
            "quantity": int(product.quantity),
        }
        template = product.main_template_id
        # Send out_of_stock only if filled. If not it means we do not manage it and
        # we do not want to set it to refuse order by default
        if template.out_of_stock:
            vals["out_of_stock"] = int(template.out_of_stock)
        return vals
