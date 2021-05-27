# © 2018 PlanetaTIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from os.path import dirname, join
from unittest import mock

from odoo.addons.connector_prestashop.tests.common import PrestashopTransactionCase


class CatalogManagerTransactionCase(PrestashopTransactionCase):
    def setUp(self):
        super().setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env["prestashop.shop.group"].search([])
        self.shop = self.env["prestashop.shop"].search([])

        mock_delay_record = mock.MagicMock()
        self.instance_delay_record = mock_delay_record.return_value
        self.patch_delay_record = mock.patch(
            "odoo.addons.queue_job.models.base.DelayableRecordset",
            new=mock_delay_record,
        )
        self.patch_delay_record.start()

        self.cassette_library_dir = join(dirname(__file__), "fixtures/cassettes")

    def tearDown(self):
        super().tearDown()
        self.patch_delay_record.stop()
