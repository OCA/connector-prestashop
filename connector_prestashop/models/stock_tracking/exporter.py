# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from openerp import _
from openerp.exceptions import Warning as UserError
from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.queue.job import job
from ...backend import prestashop
from ...unit.backend_adapter import PrestaShopCRUDAdapter
from ...connector import get_environment

_logger = logging.getLogger(__name__)


@prestashop
class PrestashopTrackingExporter(Exporter):
    _model_name = ['prestashop.sale.order']

    def _get_tracking(self):
        trackings = []
        for picking in self.binding.picking_ids:
            if picking.carrier_tracking_ref:
                trackings.append(picking.carrier_tracking_ref)
        return ';'.join(trackings) if trackings else None

    def run(self, binding_id):
        """ Export the tracking number of a picking to Magento """
        # verify the picking is done + magento id exists
        tracking_adapter = self.unit_for(
            PrestaShopCRUDAdapter, '__not_exit_prestashop.order_carrier')

        self.binding = self.env[self.model._name].browse(binding_id)
        tracking = self._get_tracking()
        if tracking:
            prestashop_order_id = self.binder.to_backend(binding_id)
            filters = {
                'filter[id_order]': prestashop_order_id,
            }
            order_carrier_id = tracking_adapter.search(filters)
            if order_carrier_id:
                order_carrier_id = order_carrier_id[0]
                vals = tracking_adapter.read(order_carrier_id)
                vals['tracking_number'] = tracking
                tracking_adapter.write(order_carrier_id, vals)
                return "Tracking %s exported" % tracking
            else:
                raise UserError(_('No carrier found on sale order'))
        else:
            return "No tracking to export"


@job
def export_tracking_number(session, model_name, record_id):
    """ Export the tracking number of a delivery order. """
    order = session.browse(model_name, record_id)
    backend_id = order.backend_id.id
    env = get_environment(session, model_name, backend_id)
    tracking_exporter = env.get_connector_unit(PrestashopTrackingExporter)
    return tracking_exporter.run(record_id)
