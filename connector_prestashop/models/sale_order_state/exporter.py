# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.queue_job.job import job
from odoo.addons.connector.unit.synchronizer import Exporter
from ...backend import prestashop


# # @prestashop
class SaleStateExporter(Exporter):
    _model_name = ['prestashop.sale.order']

    def run(self, prestashop_id, state, **kwargs):
        datas = {
            'order_history': {
                'id_order': prestashop_id,
                'id_order_state': state,
            }
        }
        self.backend_adapter.update_sale_state(prestashop_id, datas)


def find_prestashop_state(session, sale_state, backend):
    state_list_model = session.env['sale.order.state.list']
    state_lists = state_list_model.search(
        [('name', '=', sale_state)]
    )
    for state_list in state_lists:
        if state_list.prestashop_state_id.backend_id == backend:
            return state_list.prestashop_state_id.prestashop_id
    return None


@job
def export_sale_state(session, model_name, record_id):
    binding_model = session.env[model_name]
    sales = binding_model.search([('odoo_id', '=', record_id)])
    for sale in sales:
        backend = sale.backend_id
        new_state = find_prestashop_state(session, sale.state, backend)
        if not new_state:
            continue
        env = backend.get_environment(binding_model._name, session=session)
        sale_exporter = env.get_connector_unit(SaleStateExporter)
        sale_exporter.run(sale.prestashop_id, new_state)
