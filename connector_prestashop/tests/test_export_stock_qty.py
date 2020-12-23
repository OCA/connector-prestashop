# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

from .common import ExportStockQuantityCase, assert_no_job_delayed


class TestExportStockQuantity(ExportStockQuantityCase):
    @assert_no_job_delayed
    def test_export_stock_qty_delay(self):
        """ Backend button delay a job to delay stock quantities export """
        delay_record_path = "odoo.addons.queue_job.models.base." "DelayableRecordset"
        with mock.patch(delay_record_path) as delay_record_mock:
            self.backend_record.update_product_stock_qty()
            delay_record_instance = delay_record_mock.return_value
            delay_record_instance.export_product_quantities.assert_called_with(
                backend=self.backend_record
            )

    @assert_no_job_delayed
    def test_job_recompute_prestashop_qty(self):
        delay_record_path = "odoo.addons.queue_job.models.base." "DelayableRecordset"

        variant_binding = self._create_product_binding(
            name="Faded Short Sleeves T-shirt",
            template_ps_id=1,
            variant_ps_id=1,
        )
        base_qty = variant_binding.qty_available
        base_prestashop_qty = variant_binding.quantity
        self.assertEqual(0, base_qty)
        self.assertEqual(0, base_prestashop_qty)

        with mock.patch(delay_record_path) as delay_record_mock:
            self.env["prestashop.product.template"].export_product_quantities(
                self.backend_record
            )
            # no job delayed because no quantity has been changed
            delay_record_instance = delay_record_mock.return_value
            self.assertEqual(0, delay_record_instance.export_inventory.call_count)

        self._change_product_qty(variant_binding.odoo_id, 42)
        with mock.patch(delay_record_path) as delay_record_mock:
            variant_binding.with_context(
                connector_no_export=False
            ).recompute_prestashop_qty()
            delay_record_instance = delay_record_mock.return_value
            self.assertEqual(1, delay_record_instance.export_inventory.call_count)
            delay_record_instance.export_inventory.assert_called_with(
                fields=["quantity"]
            )

        self._change_product_qty(variant_binding.odoo_id, 42)
        # problem is there is not api.depends ok template qty field
        with mock.patch(delay_record_path) as delay_record_mock:
            # the function call the update qty for template and combination
            # depending on the state of the tests we may have one or two call
            self.env["prestashop.product.template"].export_product_quantities(
                self.backend_record
            )
            delay_record_instance = delay_record_mock.return_value
            self.assertGreater(delay_record_instance.export_inventory.call_count, 0)
