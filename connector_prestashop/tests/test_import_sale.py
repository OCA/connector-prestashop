# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

import mock

from freezegun import freeze_time

from .common import recorder, PrestashopTransactionCase, assert_no_job_delayed


ExpectedSale = namedtuple(
    'ExpectedSale',
    'name carrier_id total_amount partner_id partner_invoice_id '
    'partner_shipping_id pricelist_id payment_mode_id'
)

ExpectedSaleLine = namedtuple(
    'ExpectedSaleLine',
    'name product_id price_unit product_uom_qty'
)


class TestImportSale(PrestashopTransactionCase):
    """ Test the import of partner from PrestaShop """

    def setUp(self):
        super(TestImportSale, self).setUp()
        self.sync_metadata()
        self.base_mapping()

        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

    @freeze_time('2016-12-09 00:00:00')
    @assert_no_job_delayed
    def test_import_sales(self):
        from_date = '2016-12-01 00:00:00'
        self.backend_record.import_orders_since = from_date
        import_job = ('openerp.addons.connector_prestashop.models'
                      '.binding.common'
                      '.import_bacth')
        with mock.patch(import_job) as import_mock:
            self.backend_record.import_sale_orders()
            import_mock.delay.assert_called_with(
                mock.ANY, self.backend_record.id,
                from_date,
                priority=5,
            )

    @freeze_time('2016-12-09 00:00:00')
    @assert_no_job_delayed
    def test_import_sale_batch(self):
        from_date = '2016-12-01 00:00:00'
        self.backend_record.import_res_partner_from_date = from_date
        record_job_path = ('openerp.addons.connector_prestashop.models'
                           '.binding.common.import_batch')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette('test_import_sale_batch') as cassette, \
                mock.patch(record_job_path) as import_record_mock:

            self.env['prestashop.sale.order'].import_orders_since(
                self.backend_record,
                from_date,
            )

            expected_query = {
                'date': ['1'],
                'limit': ['0,1000'],
                'filter[date_upd]': ['>[2016-12-01 00:00:00]'],
            }
            self.assertEqual(2, len(cassette.requests))

            request = cassette.requests[0]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/orders', self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            expected_query = {
                'date': ['1'],
                'limit': ['0,1000'],
                'filter[date_add]': ['>[2016-12-01 00:00:00]'],
            }
            request = cassette.requests[1]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/customer_messages',
                             self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            self.assertEqual(5, import_record_mock.delay.call_count)

    @assert_no_job_delayed
    def test_import_sale_record(self):
        """ Import a sale order """
        # setup for sale order with id 5, create the dependencies
        mode_journal = self.env['account.journal'].search([], limit=1)
        payment_method_xmlid = 'account.account_payment_method_manual_in'
        payment_method = self.env.ref(payment_method_xmlid)
        payment_mode = self.env['account.payment.mode'].create({
            'name': 'Bank wire',
            'company_id': self.backend_record.company_id.id,
            'bank_account_link': 'fixed',
            'fixed_journal_id': mode_journal.id,
            'payment_type': 'inbound',
            'payment_method_id': payment_method.id,
        })

        ship_product = self.env.ref(
            'connector_ecommerce.product_product_shipping'
        )

        carrier = self.env['delivery.carrier'].create({
            'name': 'My carrier',
            'product_id': ship_product.id,
            'partner_id': self.env.ref('base.main_company').partner_id.id,
        })
        self.create_binding_no_export(
            'prestashop.delivery.carrier', carrier.id, prestashop_id=2,
        )

        variant_tshirt_orange_s_binding = self._create_product_binding(
            name='Faded Short Sleeve T-shirts',
            template_ps_id=1,
            variant_ps_id=1,
        )
        variant_tshirt_orange_s = variant_tshirt_orange_s_binding.odoo_id
        variant_blouse_black_s_binding = self._create_product_binding(
            name='Blouse',
            template_ps_id=2,
            variant_ps_id=7,
        )
        variant_blouse_black_s = variant_blouse_black_s_binding.odoo_id
        variant_dress_orange_s_binding = self._create_product_binding(
            name='Printed Dress',
            template_ps_id=3,
            variant_ps_id=13,
        )
        variant_dress_orange_s = variant_dress_orange_s_binding.odoo_id

        partner = self.env['res.partner'].create({
            'name': 'John DOE',
        })
        partner_binding = self.create_binding_no_export(
            'prestashop.res.partner', partner.id, prestashop_id=1,
            shop_group_id=self.shop.id,
        )
        address = self.env['res.partner'].create({
            'name': 'John DOE',
            'parent_id': partner.id,
        })
        self.create_binding_no_export(
            'prestashop.address', address.id, prestashop_id=4,
            prestashop_partner_id=partner_binding.id
        )

        # import of the sale order
        with recorder.use_cassette('test_import_sale_record_5'):
            result = self.env['prestashop.sale.order'].import_record(
                self.backend_record, 5)

        error_msg = ('Import of the order 5 canceled '
                     'because it has not been paid since 30 days')
        self.assertEqual(result, error_msg)

        with recorder.use_cassette('test_import_sale_record_5'):
            with freeze_time("2016-12-08"):
                self.env['prestashop.sale.order'].import_record(
                    self.backend_record, 5)

        domain = [('prestashop_id', '=', 5),
                  ('backend_id', '=', self.backend_record.id)]
        binding = self.env['prestashop.sale.order'].search(domain)
        binding.ensure_one()

        expected = [
            ExpectedSale(
                name='KHWLILZLL',
                partner_id=partner,
                partner_invoice_id=address,
                partner_shipping_id=address,
                total_amount=71.51,
                carrier_id=carrier,
                payment_mode_id=payment_mode,
                pricelist_id=self.backend_record.pricelist_id,
            )]

        self.assert_records(expected, binding)

        expected = [
            ExpectedSaleLine(
                name='Faded Short Sleeve T-shirts - Color : Orange, Size : S',
                product_id=variant_tshirt_orange_s,
                price_unit=16.51,
                product_uom_qty=1.0,
            ),
            ExpectedSaleLine(
                name='Blouse - Color : Black, Size : S',
                product_id=variant_blouse_black_s,
                price_unit=27.0,
                product_uom_qty=1.0,
            ),
            ExpectedSaleLine(
                name='Printed Dress - Color : Orange, Size : S',
                product_id=variant_dress_orange_s,
                price_unit=26.0,
                product_uom_qty=1.0,
            ),
            ExpectedSaleLine(
                name='My carrier',
                product_id=ship_product,
                price_unit=2.0,
                product_uom_qty=1.0,
            ),
        ]

        self.assert_records(expected, binding.order_line)
