# © 2018 PlanetaTIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector_prestashop.tests.common import (
    assert_no_job_delayed,
    recorder,
)

from .common import CatalogManagerTransactionCase


class TestExportProductAttribute(CatalogManagerTransactionCase):
    def setUp(self):
        super().setUp()

        # create and bind attribute
        attribute_size = self.env["product.attribute"].create(
            {
                "name": "Size",
            }
        )
        self.create_binding_no_export(
            "prestashop.product.combination.option", attribute_size.id, 1
        )

        # create attribute and value
        self.attribute = self.env["product.attribute"].create(
            {
                "name": "New attribute",
            }
        )
        self.value = self.env["product.attribute.value"].create(
            {
                "attribute_id": attribute_size.id,
                "name": "New value",
            }
        )

    def _bind_attribute(self):
        return self.create_binding_no_export(
            "prestashop.product.combination.option", self.attribute.id, 4
        ).with_context(connector_no_export=False)

    def _bind_value(self):
        return self.create_binding_no_export(
            "prestashop.product.combination.option.value", self.value.id, 25
        ).with_context(connector_no_export=False)

    @assert_no_job_delayed
    def test_export_product_attribute_onbind(self):
        # create attribute binding
        self.env["prestashop.product.combination.option"].create(
            {
                "backend_id": self.backend_record.id,
                "odoo_id": self.attribute.id,
            }
        )
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_attribute_value_onbind(self):
        # bind attribute
        self._bind_attribute()
        # create value binding
        self.env["prestashop.product.combination.option.value"].create(
            {
                "backend_id": self.backend_record.id,
                "odoo_id": self.value.id,
            }
        )
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_attribute_onwrite(self):
        # bind attribute
        self._bind_attribute()
        # check no export delayed
        self.assertEqual(0, self.instance_delay_record.export_record.call_count)
        # write in value
        self.attribute.name = "New attribute updated"
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)
        # write in binding
        # binding.display_type = "radio" --> This triggered below 2 events
        # attribute.event.listener.on_record_write calling export_record
        # prestashop.attribute.event.listener.on_record_write calling export_record
        self.attribute.display_type = "radio"
        # check export delayed again
        self.assertEqual(2, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_attribute_value_onwrite(self):
        # bind attribute and value
        self._bind_attribute()
        binding = self._bind_value()
        # check no export delayed
        self.assertEqual(0, self.instance_delay_record.export_record.call_count)
        # write in value
        self.value.name = "New value updated"
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)
        # write in binding
        binding.prestashop_position = 2
        # check export delayed again
        self.assertEqual(2, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_attribute_job(self):
        # create attribute binding
        binding = self.env["prestashop.product.combination.option"].create(
            {
                "backend_id": self.backend_record.id,
                "odoo_id": self.attribute.id,
                "group_type": "select",
                "prestashop_position": 4,
            }
        )
        # export attribute
        with recorder.use_cassette(
            "test_export_product_attribute",
            cassette_library_dir=self.cassette_library_dir,
        ) as cassette:
            binding.export_record()

            # check request
            self.assertEqual(1, len(cassette.requests))
            request = cassette.requests[0]
            self.assertEqual("POST", request.method)
            self.assertEqual("/api/product_options", self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
            body = self.xmltodict(request.body)
            ps_option = body["prestashop"]["product_options"]
            # check basic fields
            for field, value in list(
                {
                    "group_type": "select",
                    "position": "4",
                }.items()
            ):
                self.assertEqual(value, ps_option[field])
            # check translatable fields
            for field, value in list(
                {
                    "name": "New attribute",
                    "public_name": "New attribute",
                }.items()
            ):
                self.assertEqual(value, ps_option[field]["language"]["value"])

    @assert_no_job_delayed
    def test_export_product_attribute_value_job(self):
        # create value binding
        binding = self.env["prestashop.product.combination.option.value"].create(
            {
                "backend_id": self.backend_record.id,
                "odoo_id": self.value.id,
            }
        )
        # export value
        with recorder.use_cassette(
            "test_export_product_attribute_value",
            cassette_library_dir=self.cassette_library_dir,
        ) as cassette:
            binding.export_record()

            # check request
            self.assertEqual(1, len(cassette.requests))
            request = cassette.requests[0]
            self.assertEqual("POST", request.method)
            self.assertEqual("/api/product_option_values", self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
            body = self.xmltodict(request.body)
            ps_option = body["prestashop"]["product_option_value"]
            # check basic fields
            for field, value in list(
                {
                    "id_attribute_group": "1",
                    "value": "New value",
                }.items()
            ):
                self.assertEqual(value, ps_option[field])
            # check translatable fields
            for field, value in list(
                {
                    "name": "New value",
                }.items()
            ):
                self.assertEqual(value, ps_option[field]["language"]["value"])
