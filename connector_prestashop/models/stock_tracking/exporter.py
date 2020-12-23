# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import FailedJobError


class PrestashopTrackingExporter(Component):
    _name = "prestashop.stock.tracking.exporter"
    _inherit = "prestashop.exporter"
    _apply_on = ["prestashop.sale.order"]
    _usage = "tracking.exporter"

    def _get_tracking(self):
        trackings = []
        for picking in self.binding.picking_ids:
            if picking.carrier_tracking_ref:
                trackings.append(picking.carrier_tracking_ref)
        return " ".join(trackings) if trackings else None

    def run(self, binding, **kwargs):
        """ Export the tracking number of a picking to PrestaShop """
        # verify the picking is done + prestashop id exists
        tracking_adapter = self.component(
            usage="backend.adapter", model_name="__not_exit_prestashop.order_carrier"
        )
        self.binding = binding
        tracking = self._get_tracking()
        if tracking:
            prestashop_order_id = self.binder.to_external(self.binding)
            filters = {
                "filter[id_order]": prestashop_order_id,
            }
            order_carrier_id = tracking_adapter.search(filters)
            if order_carrier_id:
                order_carrier_id = order_carrier_id[0]
                vals = tracking_adapter.read(order_carrier_id)
                vals["tracking_number"] = tracking
                tracking_adapter.write(order_carrier_id, vals)
                return "Tracking %s exported" % tracking
            else:
                raise FailedJobError("No carrier found on sale order")
        else:
            return "No tracking to export"
