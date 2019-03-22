# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

from .common import (
    recorder, PrestashopTransactionCase, quiet_logger, assert_no_job_delayed
)

ExpectedShopGroup = namedtuple('ExpectedShopGroup',
                               'name prestashop_id backend_id')

ExpectedShop = namedtuple('ExpectedShop',
                          'name prestashop_id odoo_id shop_group_id '
                          'backend_id')


class TestImportBackendData(PrestashopTransactionCase):

    def setUp(self):
        super(TestImportBackendData, self).setUp()

    @recorder.use_cassette
    @assert_no_job_delayed
    def test_import_metadata(self):
        """ Import shop groups and shops """
        self.backend_record.synchronize_metadata()

        shop_groups = self.env['prestashop.shop.group'].search([])
        self.assertEqual(len(shop_groups), 1)
        expected = [
            ExpectedShopGroup(
                name='Default',
                prestashop_id=1,
                backend_id=self.backend_record,
            ),
        ]
        self.assert_records(expected, shop_groups)

        shops = self.env['prestashop.shop'].search([])
        self.assertEqual(len(shops), 1)
        expected = [
            ExpectedShop(
                name='PrestaShop',
                prestashop_id=1,
                odoo_id=self.backend_record.warehouse_id,
                shop_group_id=shop_groups,
                backend_id=self.backend_record,
            ),
        ]
        self.assert_records(expected, shops)

    @recorder.use_cassette
    @assert_no_job_delayed
    def test_import_basedata(self):
        """ Import base data (langs, countries, currencies, taxes) """
        # ensure it is created afresh from the sync
        self.env['prestashop.res.lang'].search([]).unlink()
        self.configure_taxes()
        auto_import_logger = (
            'odoo.addons.connector_prestashop.components.'
            'auto_matching_importer'
        )
        with quiet_logger('vcr'), quiet_logger('urllib3'):
            with quiet_logger(auto_import_logger):
                self.backend_record.synchronize_basedata()

        langs = self.env['prestashop.res.lang'].search([])
        self.assertEqual(len(langs), 1)

        countries = self.env['prestashop.res.country'].search([])
        self.assertEqual(len(countries), 243)

        currencies = self.env['prestashop.res.currency'].search([])
        self.assertEqual(len(currencies), 1)

        taxes = self.env['prestashop.account.tax'].search([])
        self.assertEqual(len(taxes), 7)
