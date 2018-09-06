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


class TestImportInventory(PrestashopTransactionCase):
    """ Test the import of partner from PrestaShop """

    def setUp(self):
        super(TestImportInventory, self).setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

    @assert_no_job_delayed
    def test_import_inventory_delay(self):
        """ Backend button delay a job to delay inventory import """
        delay_record_path = ('odoo.addons.queue_job.models.base.'
                             'DelayableRecordset')
        with mock.patch(delay_record_path) as delay_record_mock:
            self.backend_record.import_stock_qty()
            delay_record_instance = delay_record_mock.return_value
            delay_record_instance.import_inventory.assert_called_with(
                self.backend_record)

    @assert_no_job_delayed
    def test_import_inventory_batch(self):
        delay_record_path = ('odoo.addons.queue_job.models.base.'
                             'DelayableRecordset')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette('test_import_inventory_batch') as cassette,\
                mock.patch(delay_record_path) as delay_record_mock:

            self.env['prestashop.product.template'].import_inventory(
                self.backend_record)
            expected_query = {
                'display': ['[id,id_product,id_product_attribute]'],
                'limit': ['0,1000'],
            }
            # 1 request to get 52 stocks
            # 7 requests to check if there are stocks for product combinations
            self.assertEqual(8, len(cassette.requests))

            request = cassette.requests[0]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/stock_availables',
                             self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            # 7 product stocks are skipped because combination stocks will be
            # imported
            delay_record_instance = delay_record_mock.return_value
            self.assertEqual(
                45, delay_record_instance.import_record.call_count)

    @assert_no_job_delayed
    def test_import_inventory_record_template(self):
        """ Import the inventory for a template"""
        variant_binding = self._create_product_binding(
            name='Faded Short Sleeves T-shirt',
            template_ps_id=1,
            variant_ps_id=1,
        )

        template = variant_binding.odoo_id.product_tmpl_id

        self.assertEqual(0, template.qty_available)
        with recorder.use_cassette('test_import_inventory_record_template_1'):
            self.env['_import_stock_available'].import_record(
                self.backend_record, 1,
                # id_product_attribute='0' means we
                # import the template quantity
                record={'id_product_attribute': '0',
                        'id': '1',
                        'id_product': '1'})
        # cumulative stock of all the variants
        template = self.env['product.template'].browse(template.id)
        self.assertEqual(1799, template.qty_available)

    @assert_no_job_delayed
    def test_import_inventory_record_variant(self):
        """ Import the inventory for a variant"""
        variant_binding = self._create_product_binding(
            name='Faded Short Sleeves T-shirt',
            template_ps_id=1,
            variant_ps_id=1,
        )

        template = variant_binding.odoo_id.product_tmpl_id

        self.assertEqual(0, template.qty_available)
        with recorder.use_cassette('test_import_inventory_record_variant_1'):
            self.env['_import_stock_available'].import_record(
                self.backend_record, 1,
                record={'id_product_attribute': '1',
                        'id': '1',
                        'id_product': '1'})
        template = self.env['product.template'].browse(template.id)
        self.assertEqual(299, template.qty_available)
