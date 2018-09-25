# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import exceptions

from .common import recorder, PrestashopTransactionCase


class TestAuth(PrestashopTransactionCase):

    @recorder.use_cassette
    def test_auth_success(self):
        self.assertEqual('draft', self.backend_record.state)
        self.backend_record.button_check_connection()
        self.assertEqual('checked', self.backend_record.state)

    @recorder.use_cassette
    def test_auth_failure(self):
        self.backend_record.webservice_key = 'xyz'
        with self.assertRaisesRegexp(exceptions.UserError,
                                     u'Connection failed'):
            self.backend_record.button_check_connection()
