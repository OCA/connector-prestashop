# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import fields, models
from odoo.tools import config

from odoo.addons.component.core import Component

from ...components.backend_adapter import PrestaShopWebServiceImage


class ProductImage(models.Model):
    _inherit = "base_multi_image.image"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.product.image",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )


class PrestashopProductImage(models.Model):
    _name = "prestashop.product.image"
    _inherit = "prestashop.binding"
    _inherits = {"base_multi_image.image": "odoo_id"}
    _description = "Product image prestashop bindings"

    odoo_id = fields.Many2one(
        comodel_name="base_multi_image.image",
        required=True,
        ondelete="cascade",
        string="Product image",
    )

    def import_product_image(self, backend, product_tmpl_id, image_id, **kwargs):
        """Import a product image"""
        with backend.work_on(self._name) as work:
            importer = work.component(usage="record.importer")
            return importer.run(product_tmpl_id, image_id)


class ProductImageAdapter(Component):
    _name = "prestashop.product.image.adapter"
    _inherit = "prestashop.crud.adapter"
    _apply_on = "prestashop.product.image"
    _prestashop_image_model = "products"
    _prestashop_model = "images/products"
    _export_node_name = "images/products"
    _export_node_name_res = "image"
    # pylint: disable=method-required-super

    def connect(self):
        debug = False
        if config["log_level"] == "debug":
            debug = True
        return PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key, debug=debug
        )

    def read(self, product_tmpl_id, image_id, options=None):
        api = self.connect()
        return api.get_image(
            self._prestashop_image_model, product_tmpl_id, image_id, options=options
        )

    def create(self, attributes=None):
        api = self.connect()
        # TODO: odoo logic in the adapter? :-(
        url = "{}/{}".format(self._prestashop_model, attributes["id_product"])
        return api.add(
            url,
            files=[
                (
                    "image",
                    attributes["filename"],
                    base64.b64decode(attributes["content"]),
                )
            ],
        )

    def write(self, id_, attributes=None):
        api = self.connect()
        # TODO: odoo logic in the adapter? :-(
        url = "{}/{}".format(self._prestashop_model, attributes["id_product"])
        url_del = "{}/{}/{}/{}".format(
            api._api_url, self._prestashop_model, attributes["id_product"], id_
        )
        try:
            api._execute(url_del, "DELETE")
        except BaseException:
            pass
        return api.add(
            url,
            files=[
                (
                    "image",
                    attributes["filename"],
                    base64.b64decode(attributes["content"]),
                )
            ],
        )

    def delete(self, resource, id_, attributes=None):
        """Delete a record on the external system"""
        api = self.connect()
        # The uri should be image/products/id_product/id_image. The url_del
        # must not include id_image. That is being done by api.delete.
        url_del = "{}/{}".format(resource, attributes["id_product"])
        return api.delete(url_del, resource_ids=id_)
