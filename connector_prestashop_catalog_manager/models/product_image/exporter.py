# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tools.translate import _

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_prestashop.components.backend_adapter import (
    PrestaShopWebServiceImage,
)


class ProductImageExporter(Component):
    _name = "prestashop.product.image.exporter"
    _inherit = "prestashop.exporter"
    _apply_on = "prestashop.product.image"

    def _run(self, fields=None):
        """Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.binding

        if self._has_to_skip():
            return

        # export the missing linked resources
        self._export_dependencies()
        map_record = self.mapper.map_record(self.binding)

        if self.prestashop_id:
            record = list(map_record.values())
            if not record:
                return _("Nothing to export.")
            # special check on data before export
            self._validate_data(record)
            exported_vals = self._update(record)
        else:
            record = map_record.values(for_create=True)
            if not record:
                return _("Nothing to export.")
            # special check on data before export
            self._validate_data(record)
            exported_vals = self._create(record)
        self._after_export()
        if (
            exported_vals
            and exported_vals.get("prestashop")
            and exported_vals["prestashop"].get("image")
        ):
            self.prestashop_id = int(exported_vals["prestashop"]["image"].get("id"))

        self._link_image_to_url()
        message = _("Record exported with ID %s on Prestashop.")
        return message % self.prestashop_id

    def _link_image_to_url(self):
        """Change image storage to a url linked to product prestashop image"""
        api = PrestaShopWebServiceImage(
            api_url=self.backend_record.location,
            api_key=self.backend_record.webservice_key,
        )
        full_public_url = api.get_image_public_url(
            {
                "id_image": str(self.prestashop_id),
                "type": "image/jpeg",
            }
        )
        if self.binding.load_from != full_public_url:
            self.binding.with_context(connector_no_export=True).write(
                {
                    "load_from": full_public_url,
                }
            )


class ProductImageExportMapper(Component):
    _name = "prestashop.product.image.mapper"
    _inherit = "prestashop.export.mapper"
    _apply_on = "prestashop.product.image"

    direct = [
        ("name", "name"),
    ]

    @mapping
    def product_id(self, record):
        if record.odoo_id.owner_model == "product.product":
            product_tmpl = (
                record.env["product.product"]
                .browse(record.odoo_id.owner_id)
                .product_tmpl_id
            )
        else:
            product_tmpl = record.env["product.template"].browse(
                record.odoo_id.owner_id
            )
        binder = self.binder_for("prestashop.product.template")
        ps_product_id = binder.to_external(product_tmpl, wrap=True)
        return {"id_product": ps_product_id}

    @mapping
    def legend(self, record):
        return {"legend": record.name}

    @mapping
    def load_from(self, record):
        return {"load_from": record.load_from}

    @mapping
    def image_1920(self, record):
        return {"image_1920": record.image_1920}
