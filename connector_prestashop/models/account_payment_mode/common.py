# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class PaymentModeAdapter(Component):
    _name = 'account.payment.mode.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'account.payment.mode'

    _model_name = 'account.payment.mode'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def search(self, filters=None):
        res = self.client.get(self._prestashop_model, options=filters)
        if not res['orders']:
            return []
        methods = res[self._prestashop_model][self._export_node_name]
        if isinstance(methods, dict):
            return [methods]
        return methods


class PaymentModeBinder(Component):
    _name = 'account.payment.mode.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'account.payment.mode'

    _model_name = 'account.payment.mode'
    _external_field = 'name'

    def to_internal(self, external_id, unwrap=False, company=None):
        if company is None:
            company = self.backend_record.company_id
        bindings = self.model.with_context(active_test=False).search(
            [(self._external_field, '=', external_id),
             ('company_id', '=', company.id),
             ]
        )
        if not bindings:
            return self.model.browse()
        bindings.ensure_one()
        return bindings

    def bind(self, external_id, binding_id):
        raise TypeError('%s cannot be synchronized' % self.model._name)
