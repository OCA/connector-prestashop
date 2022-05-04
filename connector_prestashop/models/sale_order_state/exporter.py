# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.component.core import Component


class SaleStateExporter(Component):
    _name = "prestashop.sale.order.state.exporter"
    _inherit = "prestashop.exporter"
    _apply_on = ["prestashop.sale.order"]
    _usage = "sale.order.state.exporter"

    def run(self, binding, state, **kwargs):
        datas = {
            "order_history": {
                "id_order": binding.prestashop_id,
                "id_order_state": state,
            }
        }
        self.backend_adapter.update_sale_state(binding.prestashop_id, datas)
