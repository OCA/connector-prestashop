# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import logging
import mimetypes

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class ProductImageMapper(Component):
    _name = "prestashop.product.image.import.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.product.image"
    _model_name = "prestashop.product.image"

    direct = []

    @mapping
    def from_template(self, record):
        binder = self.binder_for("prestashop.product.template")
        template = binder.to_internal(record["id_product"], unwrap=True)
        name = "{}_{}".format(template.name, record["id_image"])
        
        return {
            "owner_id": template.id,
            "owner_model": "product.template",
            "name": name,
        }

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def extension(self, record):
        return {"extension": mimetypes.guess_extension(record["type"])}

    @mapping
    def image_url(self, record):
        return {"url": record["full_public_url"]}

    @mapping
    def filename(self, record):
        return {"filename": "%s.jpg" % record["id_image"]}

    @mapping
    def storage(self, record):
        return {"storage": "url"}


class ProductImageImporter(Component):
    _name = "prestashop.product.image.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.product.image"

    def _get_prestashop_data(self):
        """Return the raw PrestaShop data for ``self.prestashop_id``"""
        adapter = self.component(usage="backend.adapter", model_name=self.model._name)
        return adapter.read(self.template_id, self.image_id)

    def run(self, template_id, image_id, **kwargs):
        self.template_id = template_id
        self.image_id = image_id
        
        template_binder = self.binder_for("prestashop.product.template")
        product_tmpl = template_binder.to_internal(template_id, unwrap=True)
        
        try:
            super().run(image_id, **kwargs)
        except PrestaShopWebServiceError as error:
            if hasattr(product_tmpl, 'prestashop_default_image_id'):
                if str(product_tmpl.prestashop_default_image_id) != str(image_id):
                    return
            _logger.warning(
                "Import of main image id %s for product %s failed: %s",
                image_id, template_id, error
            )
            return
        
        if not product_tmpl.image_1920:
            product_tmpl._compute_image_1920()
        
        if hasattr(product_tmpl, 'prestashop_default_image_id'):
            if str(product_tmpl.prestashop_default_image_id) == str(image_id):
                image_binder = self.binder_for("prestashop.product.image")
                image = image_binder.to_internal(image_id, unwrap=True)
                if image:
                    product_tmpl.image_1920 = image.image_1920

