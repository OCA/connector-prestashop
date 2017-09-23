# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo import _
from odoo.addons.connector.unit.synchronizer import Exporter
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job
from ...backend import prestashop
from ...components.backend_adapter import PrestaShopCRUDAdapter

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

    def run(self, binding_id, **kwargs):
        """ Export the tracking number of a picking to Magento """
        # verify the picking is done + magento id exists
        tracking_adapter = self.unit_for(
            PrestaShopCRUDAdapter, '__not_exit_prestashop.order_carrier')

        self.binding = self.model.browse(binding_id)
        tracking = self._get_tracking()
        if tracking:
            prestashop_order_id = self.binder.to_external(self.binding)
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
                raise UserError(
                    _('PrestaShop Error'),
                    _('No carrier found on sale order'))
        else:
            return "No tracking to export"


@job
def export_tracking_number(session, model_name, record_id):
    """ Export the tracking number of a delivery order. """
    order = session.env[model_name].browse(record_id)
    backend = order.backend_id
    env = backend.get_environment(model_name, session=session)
    tracking_exporter = env.get_connector_unit(PrestashopTrackingExporter)
    return tracking_exporter.run(record_id)
