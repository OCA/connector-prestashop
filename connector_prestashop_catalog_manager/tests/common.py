# -*- coding: utf-8 -*-
# © 2018 PlanetaTIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock
from os.path import dirname, join

from openerp.addons.connector_prestashop.tests.common import (
    PrestashopTransactionCase)


class CatalogManagerTransactionCase(PrestashopTransactionCase):

    def setUp(self):
        super(CatalogManagerTransactionCase, self).setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])

        self.mock_export_record = mock.MagicMock()
        self.patch_export_record = mock.patch(
            'openerp.addons.connector_prestashop_catalog_manager.consumer.'
            'export_record',
            new=self.mock_export_record
        )
        self.patch_export_record.start()

        self.mock_export_delete_record = mock.MagicMock()
        self.patch_export_delete_record = mock.patch(
            'openerp.addons.connector_prestashop_catalog_manager.consumer.'
            'export_delete_record',
            new=self.mock_export_delete_record
        )
        self.patch_export_delete_record.start()

        self.cassette_library_dir = join(
            dirname(__file__), 'fixtures/cassettes')

    def tearDown(self):
        super(CatalogManagerTransactionCase, self).tearDown()
        self.patch_export_record.stop()
        self.patch_export_delete_record.stop()
