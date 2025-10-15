# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import base64
import logging

from odoo import fields, models
from odoo.addons.component.core import Component
from odoo.tools import config

from ...components.backend_adapter import PrestaShopWebServiceImage

_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _inherit = "base_multi_image.image"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.product.image",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )


class BaseMultiImageOwner(models.AbstractModel):
    """Fix pour la relation image_ids qui ne fonctionne pas avec owner_id Integer"""
    _inherit = "base_multi_image.owner"

    # Override du champ pour corriger la relation
    image_ids = fields.One2many(
        comodel_name="base_multi_image.image",
        compute="_compute_image_ids",
        inverse="_inverse_image_ids",
        string="Images",
        copy=True,
    )

    def _compute_image_ids(self):
        """Récupère les images liées à cet enregistrement."""
        Image = self.env["base_multi_image.image"]
        for record in self:
            if record.id:
                record.image_ids = Image.search([
                    ("owner_model", "=", record._name),
                    ("owner_id", "=", record.id)
                ])
            else:
                record.image_ids = Image

    def _inverse_image_ids(self):
        """Gère l'écriture des images."""
        Image = self.env["base_multi_image.image"]
        for record in self:
            if not record.id:
                continue

            # Images actuellement définies dans le recordset
            new_images = record.image_ids

            # Images existantes en base
            existing_images = Image.search([
                ("owner_model", "=", record._name),
                ("owner_id", "=", record.id)
            ])

            # Pour chaque image dans le recordset
            for image in new_images:
                if not image.id:
                    # Nouvelle image : assigner l'owner
                    image.owner_model = record._name
                    image.owner_id = record.id
                elif image not in existing_images:
                    # Image existante mais pas pour cet owner : mise à jour
                    image.write({
                        'owner_model': record._name,
                        'owner_id': record.id
                    })


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
            _logger.info("Call to delete URL was failed. Ignoring error")
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