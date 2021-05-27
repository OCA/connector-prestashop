# © 2018 PlanetaTIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector_prestashop.tests.common import (
    assert_no_job_delayed,
    recorder,
)

from .common import CatalogManagerTransactionCase


class TestExportProductBrand(CatalogManagerTransactionCase):
    def setUp(self):
        super().setUp()

        # create and bind parent
        parent = self.env["product.brand"].create({"name": "Home"})
        self.create_binding_no_export("prestashop.product.brand", parent.id, 2)

        # Create a product brand to export:
        self.brand = self.env["product.brand"].create(
            {
                "name": "New brand",
            }
        )

    def _bind_brand(self):
        return self.create_binding_no_export(
            "prestashop.product.brand", self.brand.id, 12
        ).with_context(connector_no_export=False)

    @assert_no_job_delayed
    def test_export_product_brand_wizard(self):
        # export from wizard
        wizard = (
            self.env["wiz.prestashop.export.product.brand"]
            .with_context(active_ids=[self.brand.id])
            .create({})
        )
        wizard.export_product_brands()

        # check binding created
        bindings = self.env["prestashop.product.brand"].search(
            [("odoo_id", "=", self.brand.id)]
        )
        self.assertEqual(1, len(bindings))
        # check export delayed
        self.instance_delay_record.export_record.assert_called_once_with(
            fields=["backend_id", "odoo_id"]
        )

    @assert_no_job_delayed
    def test_export_product_brand_onwrite(self):
        self._bind_brand()

        # check no export delayed
        self.assertEqual(0, self.instance_delay_record.export_record.call_count)

        # write in brand
        self.brand.name = "New brand updated"
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_brand_job(self):
        # create binding
        binding = self.env["prestashop.product.brand"].create(
            {
                "backend_id": self.backend_record.id,
                "odoo_id": self.brand.id,
            }
        )
        # export brand
        with recorder.use_cassette(
            "test_export_product_brand", cassette_library_dir=self.cassette_library_dir
        ) as cassette:
            binding.export_record()

            # check request
            self.assertEqual(1, len(cassette.requests))
            request = cassette.requests[0]
            self.assertEqual("POST", request.method)
            self.assertEqual("/api/manufacturers", self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
            body = self.xmltodict(request.body)
            ps_brand = body["prestashop"]["manufacturers"]
            # check name
            for field, value in list(
                {
                    "name": "New brand",
                }.items()
            ):
                self.assertEqual(value, ps_brand[field])
