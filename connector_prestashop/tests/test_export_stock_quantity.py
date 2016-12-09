# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

from openerp.addons.connector_prestashop.models.product_template.\
    exporter import export_product_quantities, export_inventory
from .common import recorder, PrestashopTransactionCase, assert_no_job_delayed


class TestExportStockQuantity(PrestashopTransactionCase):

    def setUp(self):
        super(TestExportStockQuantity, self).setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

    @assert_no_job_delayed
    def test_export_stock_qty_delay(self):
        """ Backend button delay a job to delay stock quantities export """
        export_job = ('openerp.addons.connector_prestashop.models'
                      '.prestashop_backend.common'
                      '.export_product_quantities')
        with mock.patch(export_job) as export_mock:
            self.backend_record.update_product_stock_qty()
            export_mock.delay.assert_called_with(
                mock.ANY, self.backend_record.id,
            )

    def _change_product_qty(self, product, qty):
        location = (self.backend_record.stock_location_id or
                    self.backend_record.warehouse_id.lot_stock_id)
        vals = {
            'location_id': location.id,
            'product_id': product.id,
            'new_quantity': qty,
        }
        qty_change = self.env['stock.change.product.qty'].create(vals)
        qty_change.with_context(
            active_id=product.id,
            connector_no_export=True,
        ).change_product_qty()

    @assert_no_job_delayed
    def test_job_recompute_prestashop_qty(self):
        export_job_path = ('openerp.addons.connector_prestashop.consumer'
                           '.export_inventory')

        variant_binding = self._create_product_binding(
            name='Faded Short Sleeves T-shirt',
            template_ps_id=1,
            variant_ps_id=1,
        )
        base_qty = variant_binding.qty_available
        base_prestashop_qty = variant_binding.quantity
        self.assertEqual(0, base_qty)
        self.assertEqual(0, base_prestashop_qty)

        with mock.patch(export_job_path) as export_record_mock:
            export_product_quantities(self.conn_session,
                                      self.backend_record.ids)
            # no job delayed because no quantity has been changed
            self.assertEqual(0, export_record_mock.delay.call_count)

        self._change_product_qty(variant_binding.odoo_id, 42)

        with mock.patch(export_job_path) as export_record_mock:
            export_product_quantities(self.conn_session,
                                      self.backend_record.ids)
            self.assertEqual(1, export_record_mock.delay.call_count)
            export_record_mock.delay.assert_called_with(
                mock.ANY,
                'prestashop.product.template',
                variant_binding.main_template_id.id,
                fields=['quantity'],
                priority=20,
            )

    @assert_no_job_delayed
    def test_job_export_qty(self):
        """ Export a qty on PrestaShop """
        variant_binding = self._create_product_binding(
            name='Faded Short Sleeves T-shirt',
            template_ps_id=1,
            variant_ps_id=1,
        )
        base_qty = variant_binding.qty_available
        base_prestashop_qty = variant_binding.quantity
        self.assertEqual(0, base_qty)
        self.assertEqual(0, base_prestashop_qty)

        export_job_path = ('openerp.addons.connector_prestashop.consumer'
                           '.export_inventory')
        with mock.patch(export_job_path):
            self._change_product_qty(variant_binding.odoo_id, 42)

        cassette_name = 'test_export_stock_quantity'
        with recorder.use_cassette(cassette_name) as cassette:
            export_inventory(
                self.conn_session, 'prestashop.product.template',
                variant_binding.main_template_id.id,
                fields=['quantity'],
            )
            self.assertEqual(len(cassette.requests), 3)

            request = cassette.requests[0]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/stock_availables',
                             self.parse_path(request.uri))
            expected_query = {'filter[id_product]': ['1'],
                              'filter[id_product_attribute]': ['0']}
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            request = cassette.requests[1]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/stock_availables/1',
                             self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))

            request = cassette.requests[2]
            self.assertEqual('PUT', request.method)
            self.assertEqual('/api/stock_availables',
                             self.parse_path(request.uri))
            body = self.xmltodict(request.body)

            self.assertTrue(
                set({'depends_on_stock': '0',
                     'id': '1',
                     'id_product': '1',
                     'id_product_attribute': '0',
                     'id_shop': '1',
                     'id_shop_group': '0',
                     'out_of_stock': '2',
                     'quantity': '0'}.items())
                .issubset(set(body['prestashop']['stock_available'].items())))
            self.assertDictEqual({}, self.parse_qs(request.uri))
