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


class TestExportProductProduct(CatalogManagerTransactionCase):

    def setUp(self):
        super(TestExportProductProduct, self).setUp()

        # create and bind template
        template = self.env['product.template'].create({
            'name': 'Printed Dress',
        })
        self.main_template_id = self.create_binding_no_export(
            'prestashop.product.template', template.id, 3, **{
                'default_shop_id': self.shop.id,
                })

        # create and bind color attribute
        color_attribute = self.env['product.attribute'].create({
            'name': 'Color',
        })
        self.create_binding_no_export(
            'prestashop.product.combination.option', color_attribute.id, 3)

        # create and bind color value
        color_value = self.env['product.attribute.value'].create({
            'attribute_id': color_attribute.id,
            'name': 'Orange',
        })
        self.create_binding_no_export(
            'prestashop.product.combination.option.value', color_value.id, 13)

        # create and bind size attribute
        size_attribute = self.env['product.attribute'].create({
            'name': 'Size',
        })
        self.create_binding_no_export(
            'prestashop.product.combination.option', size_attribute.id, 1)

        # create and bind size value
        size_value = self.env['product.attribute.value'].create({
            'attribute_id': size_attribute.id,
            'name': 'One size',
        })
        self.create_binding_no_export(
            'prestashop.product.combination.option.value', size_value.id, 4)

        # create product
        self.product = self.env['product.product'].create({
            'attribute_value_ids': [(6, False, [
                color_value.id,
                size_value.id,
            ])],
            'barcode': '8411788010150',
            'default_code': 'demo_3_OS',
            'default_on': False,
            'impact_price': 20.,
            'product_tmpl_id': template.id,
            'standard_price': 10.,
            'weight': 0.1,
        })

    def _bind_product(self):
        return self.create_binding_no_export(
            'prestashop.product.combination', self.product.id, None, **{
                'main_template_id': self.main_template_id.id,
                'minimal_quantity': 2,
                }).with_context(connector_no_export=False)

    def test_export_product_product_oncreate(self):
        # create binding
        binding = self.env['prestashop.product.combination'].create({
            'backend_id': self.backend_record.id,
            'odoo_id': self.product.id,
            'main_template_id': self.main_template_id.id,
        })
        # check export delayed
        self.mock_export_record.delay.assert_called_once_with(
            mock.ANY, 'prestashop.product.combination', binding.id,
            priority=20)

    def test_export_product_product_onwrite(self):
        # bind product
        binding = self._bind_product()
        # check no export delayed
        self.assertEqual(0, self.mock_export_record.delay.call_count)
        # write in product
        self.product.default_code = 'demo_3_OS'
        # check export delayed
        self.assertEqual(1, self.mock_export_record.delay.call_count)
        # write in binding
        binding.minimal_quantity = 2
        # check export delayed
        self.assertEqual(2, self.mock_export_record.delay.call_count)

    @assert_no_job_delayed
    def test_export_product_product_ondelete(self):
        # bind product
        binding = self._bind_product()
        binding.prestashop_id = 46
        # delete product
        self.product.unlink()
        # check export delete delayed
        self.mock_export_delete_record.delay.assert_called_once_with(
            mock.ANY, 'prestashop.product.combination', self.backend_record.id,
            46, 'combinations/46')

    @assert_no_job_delayed
    def test_export_product_product_jobs(self):
        # bind product
        binding = self._bind_product()

        with recorder.use_cassette(
                'test_export_product_product',
                cassette_library_dir=self.cassette_library_dir) as cassette:

            # create combination in PS
            export_record(
                self.conn_session, 'prestashop.product.combination',
                binding.id)

            # check POST request
            request = cassette.requests[0]
            self.assertEqual('POST', request.method)
            self.assertEqual('/api/combinations', self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
            body = self.xmltodict(request.body)
            ps_product = body['prestashop']['combination']
            # check basic fields
            for field, value in {
                    'active': '1',
                    'default_on': '0',
                    'ean13': '8411788010150',
                    'id_product': '3',
                    'minimal_quantity': '2',
                    'price': '20.0',
                    'reference': 'demo_3_OS',
                    'weight': '0.1',
                    'wholesale_price': '10.0',
                    }.items():
                self.assertEqual(value, ps_product[field])
            # check option values
            ps_product_option_values = (
                ps_product['associations']['product_option_values']
                ['product_option_value'])
            self.assertIn({'id': '4'}, ps_product_option_values)
            self.assertIn({'id': '13'}, ps_product_option_values)

            # delete combination in PS
            export_delete_record(
                self.conn_session, 'prestashop.product.combination',
                self.backend_record.id, binding.prestashop_id,
                'combinations/%s' % binding.prestashop_id)

            # check DELETE requests
            request = cassette.requests[1]
            self.assertEqual('DELETE', request.method)
            self.assertEqual(
                '/api/combinations/%s/%s' % (
                    binding.prestashop_id, binding.prestashop_id),
                self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
