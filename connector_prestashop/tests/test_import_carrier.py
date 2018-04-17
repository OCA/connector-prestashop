# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

import mock

from .common import recorder, PrestashopTransactionCase, assert_no_job_delayed


ExpectedCarrier = namedtuple(
    'ExpectedCarrier',
    'name partner_id product_id company_id'
)


class TestImportCarrier(PrestashopTransactionCase):
    """ Test the import of partner from PrestaShop """

    def setUp(self):
        super(TestImportCarrier, self).setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

    @assert_no_job_delayed
    def test_import_carriers(self):
        import_job = ('openerp.addons.connector_prestashop.models'
                      '.binding.common'
                      '.import_record')
        with mock.patch(import_job) as import_mock:
            self.backend_record.import_carriers()
            import_mock.delay.assert_called_with(
                mock.ANY, self.backend_record.id,
                priority=10,
            )

    @assert_no_job_delayed
    def test_import_products_batch(self):
        record_job_path = ('openerp.addons.connector_prestashop.models'
                           '.binding.common.import_record')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette('test_import_carrier_batch') as cassette, \
                mock.patch(record_job_path) as import_record_mock:

            self.env['prestashop.delivery.carrier'].import_batch(
                self.backend_record,
            )
            expected_query = {
                'filter[deleted]': ['0'],
            }
            self.assertEqual(1, len(cassette.requests))

            request = cassette.requests[0]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/carriers', self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            self.assertEqual(2, import_record_mock.delay.call_count)

    @assert_no_job_delayed
    def test_import_carrier_record(self):
        """ Import a carrier """
        with recorder.use_cassette('test_import_carrier_record_2'):
            self.env['prestashop.delivery.carrier'].import_record(
                self.backend_record, 2
            )
        domain = [('prestashop_id', '=', 2),
                  ('backend_id', '=', self.backend_record.id)]
        binding = self.env['prestashop.delivery.carrier'].search(domain)
        binding.ensure_one()

        ship_product_xmlid = 'connector_ecommerce.product_product_shipping'
        ship_product = self.env.ref(ship_product_xmlid)
        expected = [
            ExpectedCarrier(
                name='My carrier',
                partner_id=self.backend_record.company_id.partner_id,
                product_id=ship_product,
                company_id=self.backend_record.company_id,
            )]

        self.assert_records(expected, binding)
