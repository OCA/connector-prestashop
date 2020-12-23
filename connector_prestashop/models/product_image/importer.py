# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import logging
import mimetypes

from odoo import _

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

    direct = [
        # ('content', 'file_db_store'),
    ]

    @mapping
    def from_template(self, record):
        binder = self.binder_for("prestashop.product.template")
        template = binder.to_internal(record["id_product"], unwrap=True)
        name = "{}_{}".format(template.name, record["id_image"])
        return {"owner_id": template.id, "name": name}

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
        # return {'storage': 'db'}

    @mapping
    def owner_model(self, record):
        return {"owner_model": "product.template"}


class ProductImageImporter(Component):
    _name = "prestashop.product.image.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.product.image"

    def _get_prestashop_data(self):
        """ Return the raw PrestaShop data for ``self.prestashop_id`` """
        adapter = self.component(usage="backend.adapter", model_name=self.model._name)
        return adapter.read(self.template_id, self.image_id)

    def run(self, template_id, image_id, **kwargs):
        self.template_id = template_id
        self.image_id = image_id

        try:
            super(ProductImageImporter, self).run(image_id, **kwargs)
        except PrestaShopWebServiceError as error:
            binder = self.binder_for("prestashop.product.template")
            template = binder.to_internal(template_id, unwrap=True)
            if template:
                msg = _("Import of image id `%s` failed. " "Error: `%s`") % (
                    image_id,
                    error.msg,
                )
                self.backend_record.add_checkpoint(template, message=msg)
            else:
                msg = _(
                    "Import of image id `%s` of PrestaShop product "
                    "with id `%s` failed. "
                    "Error: `%s`"
                ) % (image_id, template_id, error.msg)
                self.backend_record.add_checkpoint()
