# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Exporter
from ...connector import get_environment
from ...backend import prestashop


@prestashop
class SaleStateExporter(Exporter):
    _model_name = ['prestashop.sale.order']

    def run(self, prestashop_id, state):
        datas = {
            'order_history': {
                'id_order': prestashop_id,
                'id_order_state': state,
            }
        }
        self.backend_adapter.update_sale_state(prestashop_id, datas)


def find_prestashop_state(session, sale_state, backend_id):
    state_list_model = 'sale.order.state.list'
    state_list_ids = session.search(
        state_list_model,
        [('name', '=', sale_state)]
    )
    for state_list in session.browse(state_list_model, state_list_ids):
        if state_list.prestashop_state_id.backend_id.id == backend_id:
            return state_list.prestashop_state_id.prestashop_id
    return None


@job
def export_sale_state(session, record_id):
    inherit_model = 'prestashop.sale.order'
    sale_ids = session.search(inherit_model, [('openerp_id', '=', record_id)])
    if not isinstance(sale_ids, list):
        sale_ids = [sale_ids]
    for sale in session.browse(inherit_model, sale_ids):
        backend_id = sale.backend_id.id
        new_state = find_prestashop_state(session, sale.state, backend_id)
        if new_state is None:
            continue
        env = get_environment(session, inherit_model, backend_id)
        sale_exporter = env.get_connector_unit(SaleStateExporter)
        sale_exporter.run(sale.prestashop_id, new_state)
