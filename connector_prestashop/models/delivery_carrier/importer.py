# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class DeliveryCarrierImporter(Component):
    _name = 'prestashop.delivery.carrier.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.delivery.carrier'

    _model_name = ['prestashop.delivery.carrier']


class CarrierImportMapper(Component):
    _name = 'prestashop.delivery.carrier.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.delivery.carrier'

    _model_name = 'prestashop.delivery.carrier'
    direct = [
        ('name', 'name_ext'),
        ('name', 'name'),
        ('id_reference', 'id_reference'),
    ]

    @mapping
    def active(self, record):
        return {'active_ext': record['active'] == '1'}

    @mapping
    def product_id(self, record):
        if self.backend_record.shipping_product_id:
            return {'product_id': self.backend_record.shipping_product_id.id}
        product = self.env.ref('connector_ecommerce.product_product_shipping')
        return {'product_id': product.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


class DeliveryCarrierBatchImporter(Component):
    """ Import the PrestaShop Carriers.
    """
    _name = 'prestashop.delivery.carrier.delayed.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = 'prestashop.delivery.carrier'

    _model_name = ['prestashop.delivery.carrier']

    def run(self, filters=None, **kwargs):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters=filters)
        _logger.info('search for prestashop carriers %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id, **kwargs)
