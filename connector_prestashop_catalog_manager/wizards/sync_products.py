# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api
import logging

_logger = logging.getLogger(__name__)


class SyncProducts(models.TransientModel):
    _name = 'sync.products'

    def _bind_resync(self, product_ids):
        products = self.env['product.template'].browse(product_ids)
        for product in products:
            try:
                for bind in product.prestashop_bind_ids:
                    bind.resync()
            except Exception, e:
                _logger.info('id %s, attributes %s\n', str(product.id), e)

    @api.multi
    def sync_products(self):
        self._bind_resync(self.env.context['active_ids'])

    @api.multi
    def sync_all_products(self):
        self._bind_resync([])
