# © 2018 PlanetaTIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector_prestashop.tests.common import (
    assert_no_job_delayed,
    recorder,
)

from ..models.product_template.exporter import get_slug
from .common import CatalogManagerTransactionCase


class TestExportProduct(CatalogManagerTransactionCase):
    def setUp(self):
        super().setUp()

        # create and bind category
        category_home = self.env["product.category"].create(
            {
                "name": "Home",
            }
        )
        self.create_binding_no_export(
            "prestashop.product.category", category_home.id, 2
        )
        category_women = self.env["product.category"].create(
            {
                "name": "Women",
                "parent_id": category_home.id,
            }
        )
        self.create_binding_no_export(
            "prestashop.product.category", category_women.id, 3
        )
        category_tops = self.env["product.category"].create(
            {
                "name": "Tops",
                "parent_id": category_women.id,
            }
        )
        self.create_binding_no_export(
            "prestashop.product.category", category_tops.id, 4
        )
        category_tshirts = self.env["product.category"].create(
            {
                "name": "T-shirts",
                "parent_id": category_tops.id,
            }
        )
        self.create_binding_no_export(
            "prestashop.product.category", category_tshirts.id, 5
        )

        acme_brand = self.env["product.brand"].create(
            {
                "name": "ACME",
            }
        )
        self.create_binding_no_export("prestashop.product.brand", acme_brand.id, 1)

        # create template
        self.template = self.env["product.template"].create(
            {
                "barcode": "8411788010150",
                "categ_ids": [
                    (
                        6,
                        False,
                        [
                            category_home.id,
                            category_women.id,
                            category_tops.id,
                            category_tshirts.id,
                        ],
                    )
                ],
                "default_code": "NEW_PRODUCT",
                "list_price": 20.0,
                "name": "New product",
                "prestashop_default_category_id": category_tshirts.id,
                "standard_price": 10.0,
                "weight": 0.1,
                "product_brand_id": acme_brand.id,
            }
        )

    def _bind_template(self):
        return self.create_binding_no_export(
            "prestashop.product.template",
            self.template.id,
            8,
            **{
                "default_shop_id": self.shop.id,
                "link_rewrite": "new-product",
            }
        ).with_context(connector_no_export=False)

    @assert_no_job_delayed
    def test_export_product_template_wizard_export(self):
        # export from wizard
        wizard = (
            self.env["export.multiple.products"]
            .with_context(active_ids=[self.template.id])
            .create({})
        )
        wizard.export_products()

        # check binding created
        binding_model = "prestashop.product.template"
        bindings = self.env[binding_model].search([("odoo_id", "=", self.template.id)])
        self.assertEqual(1, len(bindings))
        # check export delayed
        # sequence of fields is from ./wizards/export_multiple_products.py
        # > def create_prestashop_template
        self.instance_delay_record.export_record.assert_called_once_with(
            fields=["backend_id", "default_shop_id", "link_rewrite", "odoo_id"]
        )

    @assert_no_job_delayed
    def test_export_product_template_wizard_active(self):
        # bind template
        self._bind_template()
        # check no export delayed
        self.assertEqual(0, self.instance_delay_record.export_record.call_count)
        # deactivate from wizard
        wizard = (
            self.env["active.deactive.products"]
            .with_context(active_ids=[self.template.id])
            .create({})
        )
        wizard.deactive_products()
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)
        # deactivate again
        wizard.deactive_products()
        # check no export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)
        # force deactivate
        wizard.force_status = True
        wizard.deactive_products()
        # check export delayed
        self.assertEqual(2, self.instance_delay_record.export_record.call_count)
        # activate from wizard
        wizard.force_status = False
        wizard.active_products()
        # check export delayed
        self.assertEqual(3, self.instance_delay_record.export_record.call_count)
        # activate again
        wizard.active_products()
        # check no export delayed
        self.assertEqual(3, self.instance_delay_record.export_record.call_count)
        # force activate
        wizard.force_status = True
        wizard.active_products()
        # check export delayed
        self.assertEqual(4, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_template_wizard_resync(self):
        # bind template
        self._bind_template()
        # resync from wizard
        wizard = (
            self.env["sync.products"]
            .with_context(active_ids=[self.template.id], connector_delay=True)
            .create({})
        )
        wizard.sync_products()
        # check import done
        self.instance_delay_record.import_record.assert_called_once_with(
            self.backend_record, 8
        )

    @assert_no_job_delayed
    def test_export_product_template_onwrite(self):
        # bind template
        binding = self._bind_template()
        # check no export delayed
        self.assertEqual(0, self.instance_delay_record.export_record.call_count)
        # write in template
        self.template.name = "New product updated"
        # check export delayed
        self.assertEqual(1, self.instance_delay_record.export_record.call_count)
        # write in binding
        binding.meta_title = "New product meta title updated"
        # check export delayed
        self.assertEqual(2, self.instance_delay_record.export_record.call_count)

    @assert_no_job_delayed
    def test_export_product_template_job(self):
        # create binding
        binding = self.env["prestashop.product.template"].create(
            {
                "backend_id": self.backend_record.id,
                "odoo_id": self.template.id,
                "additional_shipping_cost": 1.0,
                "always_available": True,
                "available_date": "2016-08-29",
                "available_later": "New product available later",
                "available_now": "New product available now",
                "default_shop_id": self.shop.id,
                "description_html": "New product description",
                "description_short_html": "New product description short",
                "link_rewrite": get_slug(self.template.name),
                "meta_title": "New product meta title",
                "meta_description": "New product meta description",
                "meta_keywords": "New product meta keywords",
                "minimal_quantity": 2,
                "on_sale": True,
                "online_only": True,
                "tags": "New product tags",
            }
        )
        # export template
        with recorder.use_cassette(
            "test_export_product_template",
            cassette_library_dir=self.cassette_library_dir,
        ) as cassette:
            binding.export_record()

            # check request
            self.assertEqual(1, len(cassette.requests))
            request = cassette.requests[0]
            self.assertEqual("POST", request.method)
            self.assertEqual("/api/products", self.parse_path(request.uri))
            self.assertDictEqual({}, self.parse_qs(request.uri))
            body = self.xmltodict(request.body)
            ps_product = body["prestashop"]["product"]
            # check basic fields
            for field, value in list(
                {
                    "active": "1",
                    "additional_shipping_cost": "1.0",
                    "available_date": "2016-08-29",
                    "available_for_order": "1",
                    "barcode": "8411788010150",
                    "id_category_default": "5",
                    "id_shop_default": "1",
                    "minimal_quantity": "2",
                    "on_sale": "1",
                    "online_only": "1",
                    "price": "20.0",
                    "reference": "NEW_PRODUCT",
                    "show_price": "1",
                    "weight": "0.1",
                    "wholesale_price": "10.0",
                    "id_manufacturer": "1",
                }.items()
            ):
                self.assertEqual(value, ps_product[field])
            # check translatable fields
            for field, value in list(
                {
                    "available_later": "New product available later",
                    "available_now": "New product available now",
                    "description": "<p>New product description</p>",
                    "description_short": "<p>New product description short" "</p>",
                    "link_rewrite": "new-product",
                    "meta_description": "New product meta description",
                    "meta_keywords": "New product meta keywords",
                    "meta_title": "New product meta title",
                    "name": "New product",
                    "tags": "New product tags",
                }.items()
            ):
                self.assertEqual(value, ps_product[field]["language"]["value"])
