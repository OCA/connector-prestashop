# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

import mock

from freezegun import freeze_time

from .common import recorder, PrestashopTransactionCase, assert_no_job_delayed


ExpectedCategory = namedtuple(
    'ExpectedCategory',
    'name'
)

ExpectedPartner = namedtuple(
    'ExpectedPartner',
    'name email newsletter company active shop_group_id shop_id '
    'default_category_id birthday'
)

ExpectedAddress = namedtuple(
    'ExpectedAddress',
    'name parent_id street street2 city zip country_id phone mobile type'
)


class TestImportPartner(PrestashopTransactionCase):
    """ Test the import of partner from PrestaShop """

    def setUp(self):
        super(TestImportPartner, self).setUp()
        self.sync_metadata()
        self.base_mapping()

        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

    @freeze_time('2016-09-13 00:00:00')
    @assert_no_job_delayed
    def test_import_partner_since(self):
        from_date = '2016-09-01 00:00:00'
        self.backend_record.import_partners_since = from_date
        import_since_job = ('openerp.addons.connector_prestashop.models'
                            '.binding.common'
                            '.import_batch')
        with mock.patch(import_since_job) as import_mock:
            self.backend_record.import_customers_since()
            import_mock.delay.assert_called_with(
                mock.ANY, self.backend_record.id,
                since_date='2016-09-01 00:00:00',
                priority=10,
            )

    @freeze_time('2016-09-13 00:00:00')
    @assert_no_job_delayed
    def test_import_partner_batch(self):
        from_date = '2016-09-01 00:00:00'
        self.backend_record.import_res_partner_from_date = from_date
        record_job_path = ('openerp.addons.connector_prestashop.models'
                           '.binding.common.import_record')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        with recorder.use_cassette('test_import_partner_batch') as cassette, \
                mock.patch(record_job_path) as import_record_mock:

            self.env['prestashop.res.partner'].import_customers_since(
                self.backend_record,
                since_date=from_date,
            )
            expected_query = {
                'date': ['1'],
                'limit': ['0,1000'],
                'filter[date_upd]': ['>[2016-09-01 00:00:00]'],
            }
            self.assertEqual(2, len(cassette.requests))

            request = cassette.requests[0]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/groups', self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            request = cassette.requests[1]
            self.assertEqual('GET', request.method)
            self.assertEqual('/api/customers', self.parse_path(request.uri))
            self.assertDictEqual(expected_query, self.parse_qs(request.uri))

            self.assertEqual(5, import_record_mock.delay.call_count)

    @assert_no_job_delayed
    def test_import_partner_category_record(self):
        """ Import a partner category """
        with recorder.use_cassette('test_import_partner_category_record_1'):
            self.env['prestashop.res.partner.category'].import_record(
                self.backend_record, 3)

        domain = [('prestashop_id', '=', 3)]
        category_model = self.env['prestashop.res.partner.category']
        category_bindings = category_model.search(domain)
        category_bindings.ensure_one()

        expected = [
            ExpectedCategory(
                name='Customer A',
            )]

        self.assert_records(expected, category_bindings)

    @assert_no_job_delayed
    def test_import_partner_record(self):
        """ Import a partner """

        category = self.env['res.partner.category'].create(
            {'name': 'Customer'}
        )
        category_binding = self.create_binding_no_export(
            'prestashop.res.partner.category', category.id, 3
        )

        batch_job_path = ('openerp.addons.connector_prestashop.models'
                          '.binding.common.import_batch')
        with recorder.use_cassette('test_import_partner_record_1'), \
                mock.patch(batch_job_path) as address_batch_mock:
            self.env['prestashop.res.partner'].import_record(
                self.backend_record, 1)
            address_batch_mock.delay.assert_called_with(
                mock.ANY,
                'prestashop.address',
                self.backend_record.id,
                filters={'filter[id_customer]': '1'},
                priority=10,
            )

        domain = [('prestashop_id', '=', 1)]
        partner_bindings = self.env['prestashop.res.partner'].search(domain)
        partner_bindings.ensure_one()

        expected = [
            ExpectedPartner(
                name='John DOE',
                email='pub# # @prestashop.com',
                newsletter=True,
                company=False,
                active=True,
                shop_group_id=self.shop_group,
                shop_id=self.shop,
                default_category_id=category_binding,
                birthday='1970-01-15',
            )]

        self.assert_records(expected, partner_bindings)

    @assert_no_job_delayed
    def test_import_partner_address_batch(self):
        record_job_path = ('openerp.addons.connector_prestashop.binding'
                           '.common.import_record')
        # execute the batch job directly and replace the record import
        # by a mock (individual import is tested elsewhere)
        cassette_name = 'test_import_partner_address_batch'
        with recorder.use_cassette(cassette_name) as cassette, \
                mock.patch(record_job_path) as import_record_mock:

            self.env['prestashop.address'].import_batch(
                self.backend_record,
                filters={'filter[id_customer]': '1'}
            )
            expected_query = {
                'limit': ['0,1000'],
                'filter[id_customer]': ['1'],
            }
            self.assertEqual(1, len(cassette.requests))
            self.assertEqual('GET', cassette.requests[0].method)
            self.assertEqual('/api/addresses',
                             self.parse_path(cassette.requests[0].uri))
            query = self.parse_qs(cassette.requests[0].uri)
            self.assertDictEqual(expected_query, query)

            self.assertEqual(2, import_record_mock.delay.call_count)

    @assert_no_job_delayed
    def test_import_partner_address_record(self):
        """ Import a partner address """

        partner = self.env['res.partner'].create(
            {'name': 'Customer'}
        )
        self.create_binding_no_export(
            'prestashop.res.partner', partner.id, 1,
            shop_group_id=self.shop_group.id,
            shop_id=self.shop.id,
        )
        with recorder.use_cassette('test_import_partner_address_record_1'):
            import_record(self.conn_session, 'prestashop.address',
                          self.backend_record.id, 1)

        domain = [('prestashop_id', '=', 1)]
        address_bindings = self.env['prestashop.address'].search(domain)
        address_bindings.ensure_one()

        expected = [
            ExpectedAddress(
                name='John DOE (My address)',
                parent_id=partner,
                street='16, Main street',
                street2='2nd floor',
                city='Paris',
                zip='75002',
                country_id=self.env.ref('base.fr'),
                phone='0102030405',
                mobile=False,
                type='other',
            )]

        self.assert_records(expected, address_bindings)
