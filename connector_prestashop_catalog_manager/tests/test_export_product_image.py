# -*- coding: utf-8 -*-
# © 2018 PlanetaTIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

from .common import CatalogManagerTransactionCase

from openerp.addons.connector_prestashop.tests.common import (
    assert_no_job_delayed,
    recorder
)
from openerp.addons.connector_prestashop.unit.deleter import (
    export_delete_record)
from openerp.addons.connector_prestashop.unit.exporter import export_record
from openerp.modules.module import get_resource_path


class TestExportProductImage(CatalogManagerTransactionCase):

    def setUp(self):
        super(TestExportProductImage, self).setUp()

        # create and bind template
        template = self.env['product.template'].create({
            'name': 'Faded Short Sleeves T-shirt',
        })
        self.create_binding_no_export(
            'prestashop.product.template', template.id, 1, **{
                'default_shop_id': self.shop.id,
                })

        # create image and binding
        self.image = self.env['base_multi_image.image'].create({
            'owner_id': template.id,
            'owner_model': 'product.template',
            'storage': 'file',
            'path': get_resource_path('connector_prestashop',
                                      'static', 'description', 'icon.png'),
        })
        self.binding = self.create_binding_no_export(
            'prestashop.product.image', self.image.id, None)

    @assert_no_job_delayed
    def test_export_product_image_onwrite(self):
        # write in image
        self.image.write({
            'path': get_resource_path('connector_prestashop_catalog_manager',
                                      'static', 'description', 'icon.png'),
        })
        # check export delayed
        self.mock_export_record.delay.assert_called_once_with(
            mock.ANY, 'prestashop.product.image', self.binding.id,
            mock.ANY, priority=20)

    @assert_no_job_delayed
    def test_export_product_image_ondelete(self):
        # bind image
        self.binding.prestashop_id = 24
        # delete image
        self.image.unlink()
        # check export delete delayed
        self.mock_export_delete_record.delay.assert_called_once_with(
            mock.ANY, 'prestashop.product.image', self.backend_record.id,
            24, 'images/products/1')

    @assert_no_job_delayed
    def test_export_product_image_jobs(self):
        with recorder.use_cassette(
                'test_export_product_image',
                cassette_library_dir=self.cassette_library_dir) as cassette:

            # create image in PS
            export_record(
                self.conn_session, 'prestashop.product.image', self.binding.id)

            # check POST request
            request = cassette.requests[0]
            self.assertEqual('POST', request.method)
            self.assertEqual('/api/images/products/1',
                             self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))

            # VCR.py does not support urllib v1 request in
            # OCA/server-tools/base_multi_image/models/image.py:
            # to get image from URL so update test is avoided
#             # update image in PS
#             prestashop_id = self.binding.prestashop_id
#             export_record(
#                 self.conn_session, 'prestashop.product.image',
#                 self.binding.id)
#
#             # check DELETE requests
#             request = cassette.requests[1]
#             self.assertEqual('DELETE', request.method)
#             self.assertEqual(
#                 '/api/images/products/1/%s' % prestashop_id,
#                 self.parse_path(request.uri))
#             self.assertDictEqual({}, self.parse_qs(request.uri))
#
#             # check POST request
#             request = cassette.requests[2]
#             self.assertEqual('POST', request.method)
#             self.assertEqual('/api/images/products/1',
#                              self.parse_path(request.uri))
#             self.assertDictEqual({}, self.parse_qs(request.uri))

            # delete image in PS
            export_delete_record(
                self.conn_session, 'prestashop.product.image',
                self.backend_record.id, self.binding.prestashop_id,
                'images/products/1')

            # check DELETE requests
            request = cassette.requests[1]
            self.assertEqual('DELETE', request.method)
            self.assertEqual(
                '/api/images/products/1/%s' % self.binding.prestashop_id,
                self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
