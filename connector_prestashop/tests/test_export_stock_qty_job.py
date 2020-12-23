# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

from .common import ExportStockQuantityCase, assert_no_job_delayed, recorder


class TestExportStockQuantity(ExportStockQuantityCase):
    @assert_no_job_delayed
    def test_job_export_qty(self):
        """ Export a qty on PrestaShop """
        variant_binding = self._create_product_binding(
            name="Faded Short Sleeves T-shirt",
            template_ps_id=1,
            variant_ps_id=1,
        )
        base_qty = variant_binding.qty_available
        base_prestashop_qty = variant_binding.quantity
        self.assertEqual(0, base_qty)
        self.assertEqual(0, base_prestashop_qty)

        delay_record_path = "odoo.addons.queue_job.models.base." "DelayableRecordset"
        with mock.patch(delay_record_path):
            self._change_product_qty(variant_binding.odoo_id, 42)

        cassette_name = "test_export_stock_quantity"
        with recorder.use_cassette(cassette_name) as cassette:
            variant_binding.main_template_id.prestashop_bind_ids.export_inventory(
                fields=["quantity"]
            )
            self.assertEqual(len(cassette.requests), 3)

            request = cassette.requests[0]
            self.assertEqual("GET", request.method)
            self.assertEqual("/api/stock_availables", self.parse_path(request.uri))
            expected_query = {
                "filter[id_product]": ["1"],
                "filter[id_product_attribute]": ["0"],
            }
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            request = cassette.requests[1]
            self.assertEqual("GET", request.method)
            self.assertEqual("/api/stock_availables/1", self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))

            request = cassette.requests[2]
            self.assertEqual("PUT", request.method)
            self.assertEqual("/api/stock_availables", self.parse_path(request.uri))
            body = self.xmltodict(request.body)

            self.assertTrue(
                set(
                    {
                        "depends_on_stock": "0",
                        "id": "1",
                        "id_product": "1",
                        "id_product_attribute": "0",
                        "id_shop": "1",
                        "id_shop_group": "0",
                        "out_of_stock": "2",
                        "quantity": "0",
                    }.items()
                ).issubset(set(body["prestashop"]["stock_available"].items()))
            )
            self.assertDictEqual({}, self.parse_qs(request.uri))
