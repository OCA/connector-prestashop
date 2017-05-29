# -*- coding: utf-8 -*-
# © 2017 FactorLibre - Kiko Peiro <francisco.peiro@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop_catalog_manager import \
    product_combination
from openerp.addons.connector_prestashop.unit.exporter import export_record

_logger = logging.getLogger(__name__)


@prestashop(
    replacing=product_combination.ProductCombinationSpecificPriceExport)
class SpecificProductCombinationRecordExport(
        product_combination.ProductCombinationSpecificPriceExport):
    _model_name = 'prestashop.product.combination'

    def export_pricelist_items(self, erp_record):
        specific_price_obj = self.session.env['prestashop.specific.price']
        pricelist_id = self.backend_record.pricelist_id
        if pricelist_id:
            item_ids = self.session.env['product.pricelist.item'].search([
                ('price_version_id', '=', pricelist_id.version_id[0].id),
                ('product_id', '=', erp_record.odoo_id.id)]
            )
            for item in item_ids:
                specific_price_ext_id = specific_price_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('odoo_id', '=', item.id),
                ])
                if not specific_price_ext_id:
                    specific_price_ext_id = specific_price_obj.with_context(
                        connector_no_export=True).create({
                            'backend_id': self.backend_record.id,
                            'odoo_id': item.id,
                        })
                export_record.delay(
                    self.session,
                    'prestashop.specific.price',
                    specific_price_ext_id.id, priority=50)
