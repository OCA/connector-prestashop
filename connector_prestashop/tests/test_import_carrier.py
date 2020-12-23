# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

import mock

from .common import PrestashopTransactionCase, assert_no_job_delayed, recorder

ExpectedCarrier = namedtuple("ExpectedCarrier", "name company_id")


class TestImportCarrier(PrestashopTransactionCase):
    """ Test the import of partner from PrestaShop """

    def setUp(self):
        super(TestImportCarrier, self).setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env["prestashop.shop.group"].search([])
        self.shop = self.env["prestashop.shop"].search([])

    @assert_no_job_delayed
    def test_import_carriers(self):
        delay_record_path = "odoo.addons.queue_job.models.base." "DelayableRecordset"
        with mock.patch(delay_record_path) as delay_record_mock:
            self.backend_record.import_carriers()
            delay_record_instance = delay_record_mock.return_value
            delay_record_instance.import_batch.assert_called_with(self.backend_record)

    @assert_no_job_delayed
    def test_import_products_batch(self):
        delay_record_path = "odoo.addons.queue_job.models.base." "DelayableRecordset"
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette("test_import_carrier_batch") as cassette, mock.patch(
            delay_record_path
        ) as delay_record_mock:

            self.env["prestashop.delivery.carrier"].import_batch(
                self.backend_record,
            )
            expected_query = {
                "filter[deleted]": ["0"],
            }
            self.assertEqual(1, len(cassette.requests))

            request = cassette.requests[0]
            self.assertEqual("GET", request.method)
            self.assertEqual("/api/carriers", self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            delay_record_instance = delay_record_mock.return_value
            self.assertEqual(2, delay_record_instance.import_record.call_count)

    @assert_no_job_delayed
    def test_import_carrier_record(self):
        """ Import a carrier """
        with recorder.use_cassette("test_import_carrier_record_2"):
            self.env["prestashop.delivery.carrier"].import_record(
                self.backend_record, 2
            )
        domain = [
            ("prestashop_id", "=", 2),
            ("backend_id", "=", self.backend_record.id),
        ]
        binding = self.env["prestashop.delivery.carrier"].search(domain)
        binding.ensure_one()

        expected = [
            ExpectedCarrier(
                name="My carrier",
                company_id=self.backend_record.company_id,
            )
        ]

        self.assert_records(expected, binding)
        self.assertEqual("My carrier", binding.name)
