# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

import mock

from freezegun import freeze_time

from .common import recorder, PrestashopTransactionCase, assert_no_job_delayed


ExpectedProductCategory = namedtuple(
    'ExpectedProductCategory',
    'name odoo_id__display_name'
)

ExpectedTemplate = namedtuple(
    'ExpectedProduct',
    'name categ_id categ_ids list_price'
)

ExpectedVariant = namedtuple(
    'ExpectedVariant',
    'default_code standard_price attribute_value_ids'
)


class TestImportProduct(PrestashopTransactionCase):
    """ Test the import of partner from PrestaShop """

    def setUp(self):
        super(TestImportProduct, self).setUp()
        self.sync_metadata()
        self.base_mapping()

        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

        self.mock_delay_import_image = mock.MagicMock()
        self.patch_delay_import_image = mock.patch(
            'openerp.addons.connector_prestashop.models.product_product'
            '.common.set_product_image_variant',
            new=self.mock_delay_import_image
        )
        self.patch_delay_import_image.start()

        self.mock_delay_import_image = mock.MagicMock()
        self.patch_delay_import_image = mock.patch(
            'openerp.addons.connector_prestashop.models.product_image'
            '.common.import_product_image',
            new=self.mock_delay_import_image
        )
        self.patch_delay_import_image.start()

        self.mock_delay_set_image = mock.MagicMock()
        self.patch_delay_set_image = mock.patch(
            'openerp.addons.connector_prestashop.models.product_product'
            '.common.set_product_image_variant',
            new=self.mock_delay_set_image
        )
        self.patch_delay_set_image.start()

    def tearDown(self):
        super(TestImportProduct, self).tearDown()
        self.patch_delay_import_image.stop()
        self.patch_delay_set_image.stop()

    @freeze_time('2016-09-13 00:00:00')
    @assert_no_job_delayed
    def test_import_products(self):
        from_date = '2016-09-01 00:00:00'
        self.backend_record.import_products_since = from_date
        import_job = ('openerp.addons.connector_prestashop.models'
                      '.binding.common'
                      '.import_record')
        with mock.patch(import_job) as import_mock:
            self.backend_record.import_products()
            import_mock.delay.assert_called_with(
                mock.ANY, self.backend_record.id,
                from_date,
                priority=10,
            )

    @freeze_time('2016-09-13 00:00:00')
    @assert_no_job_delayed
    def test_import_products_batch(self):
        from_date = '2016-09-01 00:00:00'
        self.backend_record.import_products_since = from_date
        record_job_path = ('openerp.addons.connector_prestashop.models'
                           '.binding.common.import_record')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette('test_import_product_batch') as cassette, \
                mock.patch(record_job_path) as import_record_mock:

            self.env['prestashop.product.template'].import_products(
                self.backend_record,
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

    @assert_no_job_delayed
    def test_import_product_record_category(self):
        """ Import a product category """
        with recorder.use_cassette('test_import_product_category_record_1'):
            self.env['prestashop.product.category'].import_record(
                self.backend_record, 5)

        domain = [('prestashop_id', '=', 5),
                  ('backend_id', '=', self.backend_record.id)]
        binding = self.env['prestashop.product.category'].search(domain)
        binding.ensure_one()

        expected = [
            ExpectedProductCategory(
                name='T-shirts',
                odoo_id__display_name='Root / Home / Women / Tops / T-shirts',
            )]

        self.assert_records(expected, binding)

    @assert_no_job_delayed
    def test_import_product_record(self):
        """ Import a product """
        # product 1 is assigned to categories 1-5 on PrestaShop
        categs = self.env['product.category']
        for idx in range(1, 6):
            cat = self.env['product.category'].create(
                {'name': 'ps_categ_%d' % idx}
            )
            self.create_binding_no_export(
                'prestashop.product.category', cat.id, idx,
            )
            categs |= cat

        with recorder.use_cassette('test_import_product_template_record_1'):
            self.env['prestashop.product.template'].import_record(
                self.backend_record, 1)

        domain = [('prestashop_id', '=', 1),
                  ('backend_id', '=', self.backend_record.id)]
        binding = self.env['prestashop.product.template'].search(domain)
        binding.ensure_one()

        expected = [
            ExpectedTemplate(
                name='Faded Short Sleeves T-shirt',
                # For the categories, this is what I observed, not
                # necessarily what is wanted.
                categ_id=self.env.ref('product.product_category_all'),
                categ_ids=categs.filtered(lambda r: r.name != 'ps_categ_1'),
                list_price=16.51,
            )]

        self.assert_records(expected, binding)

        variants = binding.product_variant_ids

        PSValue = self.env['prestashop.product.combination.option.value']
        value_s = PSValue.search([('backend_id', '=', self.backend_record.id),
                                  ('name', '=', 'S')]).odoo_id
        value_m = PSValue.search([('backend_id', '=', self.backend_record.id),
                                  ('name', '=', 'M')]).odoo_id
        value_l = PSValue.search([('backend_id', '=', self.backend_record.id),
                                  ('name', '=', 'L')]).odoo_id
        value_orange = PSValue.search(
            [('backend_id', '=', self.backend_record.id),
             ('name', '=', 'Orange')]
        ).odoo_id
        value_blue = PSValue.search(
            [('backend_id', '=', self.backend_record.id),
             ('name', '=', 'Blue')]
        ).odoo_id

        expected_variants = [
            ExpectedVariant(
                default_code='1_1',
                standard_price=4.95,
                attribute_value_ids=value_s + value_orange,
            ),
            ExpectedVariant(
                default_code='1_2',
                standard_price=4.95,
                attribute_value_ids=value_s + value_blue,
            ),
            ExpectedVariant(
                default_code='1_3',
                standard_price=4.95,
                attribute_value_ids=value_m + value_orange,
            ),
            ExpectedVariant(
                default_code='1_4',
                standard_price=4.95,
                attribute_value_ids=value_m + value_blue,
            ),
            ExpectedVariant(
                default_code='1_5',
                standard_price=4.95,
                attribute_value_ids=value_l + value_orange,
            ),
            ExpectedVariant(
                default_code='1_6',
                standard_price=4.95,
                attribute_value_ids=value_l + value_blue,
            ),
        ]

        self.assert_records(expected_variants, variants)
