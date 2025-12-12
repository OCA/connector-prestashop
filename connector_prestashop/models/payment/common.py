# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentMethodAdapter(Component):
    _name = "account.payment.method.line.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "account.payment.method.line"

    _model_name = "account.payment.method.line"
    _prestashop_model = "orders"
    _export_node_name = "order"

    def search(self, filters=None):
        api = self.connect()
        res = api.get(self._prestashop_model, options=filters)
        methods = res[self._prestashop_model][self._export_node_name]
        if isinstance(methods, dict):
            return [methods]
        return methods
