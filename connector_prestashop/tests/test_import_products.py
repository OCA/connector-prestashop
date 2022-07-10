# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

import mock

from freezegun import freeze_time

from openerp.addons.connector_prestashop.models.\
    product_template.importer import (
        import_products
    )

from .common import recorder, PrestashopTransactionCase


ExpectedProductCategory = namedtuple(
    'ExpectedProductCategory',
    'name'
)

ExpectedProduct = namedtuple(
    'ExpectedProduct',
    'name '
)


class TestImportProduct(PrestashopTransactionCase):
    """ Test the import of partner from PrestaShop """

    def setUp(self):
        super(TestImportProduct, self).setUp()
        self.sync_metadata()
        self.base_mapping()

        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

    @freeze_time('2016-09-13 00:00:00')
    def test_import_products(self):
        from_date = '2016-09-01 00:00:00'
        self.backend_record.import_products_since = from_date
        import_job = ('openerp.addons.connector_prestashop.models'
                      '.prestashop_backend.common'
                      '.import_products')
        with mock.patch(import_job) as import_mock:
            self.backend_record.import_products()
            import_mock.delay.assert_called_with(
                mock.ANY, self.backend_record.id,
                from_date,
                priority=10,
            )

    @freeze_time('2016-09-13 00:00:00')
    def test_import_products_batch(self):
        from_date = '2016-09-01 00:00:00'
        self.backend_record.import_res_partner_from_date = from_date
        record_job_path = ('openerp.addons.connector_prestashop.unit'
                           '.importer.import_record')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette('test_import_product_batch') as cassette, \
                mock.patch(record_job_path) as import_record_mock:

            import_products(
                self.conn_session,
                self.backend_record.id,
                from_date,
            )
            expected_query = {
                'date': ['1'],
                'limit': ['0,1000'],
                'filter[date_upd]': ['>[2016-09-01 00:00:00]'],
            }
            self.assertEqual(2, len(cassette.requests))

            request = cassette.requests[0]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/categories', self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            request = cassette.requests[1]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/products', self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            self.assertEqual(18, import_record_mock.delay.call_count)
