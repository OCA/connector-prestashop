# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SyncProducts(models.TransientModel):
    _name = "sync.products"
    _description = "Synchronize Products"

    def _bind_resync(self, product_ids):
        products = self.env["product.template"].browse(product_ids)
        for product in products:
            try:
                for bind in product.prestashop_bind_ids:
                    bind.resync()
            except Exception as e:
                _logger.info("id %s, attributes %s\n", str(product.id), e)

    def sync_products(self):
        for product in self:
            product._bind_resync(product.env.context["active_ids"])

    def sync_all_products(self):
        for product in self:
            product._bind_resync([])
