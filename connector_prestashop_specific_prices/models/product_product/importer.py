# -*- coding: utf-8 -*-
# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.importer import (
    import_batch
)
from openerp.addons.connector_prestashop.models.product_product import importer

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug('Can not `from prestapyt import PrestaShopWebServiceError`.')


@prestashop(replacing=importer.ProductCombinationSpecificPriceImport)
class ProductCombinationSpecificPriceImport(
        importer.ProductCombinationSpecificPriceImport):
    _model_name = ['prestashop.product.combination']

    def import_product_specific_price(self, ps_id, erp_id):
        filters = {
            'filter[id_product_attribute]': ps_id
        }
        import_batch(
            self.session,
            'prestashop.specific.price',
            self.backend_record.id,
            filters=filters
        )
        ps_specific_prices = self.env['prestashop.specific.price']. \
            search([('product_id', '=', erp_id.id)])
        for ps_specific_price in ps_specific_prices:
            try:
                ps_specific_price.resync()
            except PrestaShopWebServiceError:
                ps_specific_price.odoo_id.unlink()
