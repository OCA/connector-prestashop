# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import namedtuple

# import mock
from os.path import dirname, join

from openerp.addons.connector_prestashop.unit.importer import (
    import_record,
)

from openerp.addons.connector_prestashop.tests.common import (
    get_recorder,
    PrestashopTransactionCase,
    assert_no_job_delayed
)


recorder = get_recorder(
    cassette_library_dir=join(dirname(__file__), 'fixtures/cassettes')
)

ExpectedManufacturer = namedtuple(
    'ExpectedManufacturer',
    'name name_ext active_ext category_id date_add date_upd'
)


class TestImportManufacturer(PrestashopTransactionCase):
    """ Test the import of manufacturer from PrestaShop """

    def setUp(self):
        super(TestImportManufacturer, self).setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env['prestashop.shop.group'].search([])
        self.shop = self.env['prestashop.shop'].search([])
        self.categ = self.env.ref(
            'connector_prestashop_manufacturer.partner_manufacturer_tag')

    @assert_no_job_delayed
    def test_import_manufacturer_record(self):
        """ Import a manufacturer """

        with recorder.use_cassette('test_import_manufacturer_record_1'):
            import_record(self.conn_session, 'prestashop.manufacturer',
                          self.backend_record.id, 1)

        domain = [('prestashop_id', '=', 1)]
        manufacturer_bindings = \
            self.env['prestashop.manufacturer'].search(domain)
        manufacturer_bindings.ensure_one()

        expected = [
            ExpectedManufacturer(
                name='John DOE',
                category_id=self.categ.id,
            )]

        self.assert_records(expected, manufacturer_bindings)
