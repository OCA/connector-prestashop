# © 2018 PlanetaTIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector_prestashop.tests.common import (
    assert_no_job_delayed,
    recorder,
)

from ..models.product_template.exporter import get_slug
from .common import CatalogManagerTransactionCase


class TestExportProductCategory(CatalogManagerTransactionCase):
    def setUp(self):
        super().setUp()

        # create and bind parent
        parent = self.env["product.category"].create({"name": "Home"})
        self.create_binding_no_export("prestashop.product.category", parent.id, 2)

        # Create a product category to export:
        self.category = self.env["product.category"].create(
            {
                "name": "New category",
                "parent_id": parent.id,
            }
        )

    def _bind_category(self):
        return self.create_binding_no_export(
            "prestashop.product.category", self.category.id, 12
        ).with_context(connector_no_export=False)

    @assert_no_job_delayed
    def test_export_product_category_wizard(self):
        # export from wizard
        wizard = (
            self.env["wiz.prestashop.export.category"]
            .with_context(active_ids=[self.category.id])
            .create({})
        )
        wizard.export_categories()

        # check binding created
        bindings = self.env["prestashop.product.category"].search(
            [("odoo_id", "=", self.category.id)]
        )
        self.assertEqual(1, len(bindings))
        # check export delayed
        # sequence of fields is from ./wizards/export_category.py
        # > def export_categories
        self.instance_delay_record.export_record.assert_called_once_with(
            fields=["backend_id", "default_shop_id", "link_rewrite", "odoo_id"]
        )

    @assert_no_job_delayed
    def test_export_product_category_onwrite(self):
        # bind category
        binding = self._bind_category()
        # check no export delayed
        self.assertEqual(0, self.instance_delay_record.export_record.call_count)

        # write in category
        self.category.name = "New category updated"
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)
        # write in binding
        binding.description = "New category description updated"
        # check export delayed again
        self.assertEqual(2, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_category_job(self):
        # create binding
        binding = self.env["prestashop.product.category"].create(
            {
                "backend_id": self.backend_record.id,
                "odoo_id": self.category.id,
                "default_shop_id": self.shop.id,
                "description": "New category description",
                "link_rewrite": get_slug(self.category.name),
                "meta_description": "New category meta description",
                "meta_keywords": "New category keywords",
                "meta_title": "New category meta title",
                "position": 1,
            }
        )
        # export category
        with recorder.use_cassette(
            "test_export_product_category",
            cassette_library_dir=self.cassette_library_dir,
        ) as cassette:
            binding.export_record()

            # check request
            self.assertEqual(1, len(cassette.requests))
            request = cassette.requests[0]
            self.assertEqual("POST", request.method)
            self.assertEqual("/api/categories", self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
            body = self.xmltodict(request.body)
            ps_category = body["prestashop"]["category"]
            # check basic fields
            for field, value in list(
                {
                    "active": "1",
                    "id_parent": "2",
                    "id_shop_default": "1",
                    "position": "1",
                }.items()
            ):
                self.assertEqual(value, ps_category[field])
            # check translatable fields
            for field, value in list(
                {
                    "description": "<p>New category description</p>",
                    "link_rewrite": "new-category",
                    "meta_description": "New category meta description",
                    "meta_keywords": "New category keywords",
                    "meta_title": "New category meta title",
                    "name": "New category",
                }.items()
            ):
                self.assertEqual(value, ps_category[field]["language"]["value"])
