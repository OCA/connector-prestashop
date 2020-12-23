# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

from .common import PrestashopTransactionCase, assert_no_job_delayed, recorder


class TestExportPicking(PrestashopTransactionCase):
    def setUp(self):
        super(TestExportPicking, self).setUp()
        self.sync_metadata()

        mock_delay_record = mock.MagicMock()
        self.instance_delay_record = mock_delay_record.return_value
        self.patch_delay_record = mock.patch(
            "odoo.addons.queue_job.models.base.DelayableRecordset",
            new=mock_delay_record,
        )
        self.patch_delay_record.start()

        stock_loc = self.ref("stock.stock_location_stock")
        customer_loc = self.ref("stock.stock_location_customers")

        self.customer_partner = self.env["res.partner"].create(
            {
                "name": "Unittest customer partner",
            }
        )

        self.shop = self.env["prestashop.shop"].search([])

        self.product_1 = self.env["product.product"].create({"name": "Blouse"})
        product_tmpl_1 = self.product_1.product_tmpl_id
        template_binding = self.create_binding_no_export(
            "prestashop.product.template",
            product_tmpl_1.id,
            prestashop_id=2,
            default_shop_id=self.shop.id,
        )
        self.create_binding_no_export(
            "prestashop.product.combination",
            self.product_1.id,
            prestashop_id=7,
            main_template_id=template_binding.id,
        )

        self.sale = self.env["sale.order"].create(
            {
                "partner_id": self.customer_partner.id,
                "partner_invoice_id": self.customer_partner.id,
                "partner_shipping_id": self.customer_partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product_1.name,
                            "product_id": self.product_1.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product_1.uom_id.id,
                        },
                    )
                ],
                "pricelist_id": self.env.ref("product.list0").id,
            }
        )

        procurement_group = self.env["procurement.group"].create(
            {
                "name": "Test",
                "move_type": "direct",
                "sale_id": self.sale.id,
            }
        )

        self.picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.ref("stock.picking_type_out"),
                "location_id": stock_loc,
                "location_dest_id": customer_loc,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Test move",
                            "sale_line_id": self.sale.order_line[0].id,
                            "product_id": self.product_1.id,
                            "product_uom": self.ref("uom.product_uom_unit"),
                            "product_uom_qty": 1,
                            "location_id": stock_loc,
                            "location_dest_id": customer_loc,
                            "group_id": procurement_group.id,
                        },
                    )
                ],
            }
        )
        self.sale.procurement_group_id = procurement_group.id

    def tearDown(self):
        super(TestExportPicking, self).tearDown()
        self.patch_delay_record.stop()

    @assert_no_job_delayed
    def test_event_tracking_number__not_prestashop_sale(self):
        """ Test that nothing is exported """
        self.picking.carrier_tracking_ref = "xyz"
        self.assertEqual(0, self.instance_delay_record.call_count)

    @assert_no_job_delayed
    def test_event_tracking_number__prestashop_sale(self):
        """ Test that tracking number is exported """
        self.create_binding_no_export(
            "prestashop.sale.order", self.sale.id, prestashop_id=2
        )
        self.picking.carrier_tracking_ref = "xyz"

        self.assertEqual(
            1, self.instance_delay_record.export_tracking_number.call_count
        )

    @assert_no_job_delayed
    def test_export_tracking_number(self):
        sale_binding = self.create_binding_no_export(
            "prestashop.sale.order", self.sale.id, prestashop_id=2
        )
        self.picking.carrier_tracking_ref = "xyz"
        cassette_name = "test_export_tracking_number"
        with recorder.use_cassette(cassette_name) as cassette:
            sale_binding.export_tracking_number()
            self.assertEqual(len(cassette.requests), 3)

            request = cassette.requests[0]
            self.assertEqual("GET", request.method)
            self.assertEqual("/api/order_carriers", self.parse_path(request.uri))
            expected_query = {"filter[id_order]": ["2"]}
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            request = cassette.requests[1]
            self.assertEqual("GET", request.method)
            self.assertEqual("/api/order_carriers/2", self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))

            request = cassette.requests[2]
            self.assertEqual("PUT", request.method)
            self.assertEqual("/api/order_carriers", self.parse_path(request.uri))
            body = self.xmltodict(request.body)
            self.assertTrue(
                set({"id": "2", "tracking_number": "xyz"}.items()).issubset(
                    set(body["prestashop"]["order_carrier"].items())
                )
            )
            self.assertDictEqual({}, self.parse_qs(request.uri))
