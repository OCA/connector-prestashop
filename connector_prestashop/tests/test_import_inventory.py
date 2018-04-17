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
        import_job = ('openerp.addons.connector_prestashop.models'
                      '.product_template.common'
                      '.import_inventory')
        with mock.patch(import_job) as import_mock:
            self.backend_record.import_stock_qty()
            import_mock.delay.assert_called_with(
                mock.ANY, self.backend_record.id,
            )

    @assert_no_job_delayed
    def test_import_inventory_batch(self):
        record_job_path = ('openerp.addons.connector_prestashop.models'
                           '.product_template.common.import_inventory')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette('test_import_inventory_batch') as cassette,\
                mock.patch(record_job_path) as import_record_mock:

            self.env['prestashop.product.template'].import_inventory(self.backend_record)
            expected_query = {
                'display': ['[id,id_product,id_product_attribute]'],
                'limit': ['0,1000'],
            }
            self.assertEqual(1, len(cassette.requests))

            request = cassette.requests[0]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/stock_availables',
                             self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            self.assertEqual(52, import_record_mock.delay.call_count)

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
        self.assertEqual(299, template.qty_available)
