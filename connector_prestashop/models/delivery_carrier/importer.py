# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.queue_job.job import job
from odoo.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper,
                                                  )
from ...unit.importer import (
    DelayedBatchImporter,
    PrestashopImporter,
    import_batch,
)
from ...backend import prestashop

_logger = logging.getLogger(__name__)


@prestashop
class DeliveryCarrierImporter(PrestashopImporter):
    _model_name = ['prestashop.delivery.carrier']


@prestashop
class CarrierImportMapper(ImportMapper):
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


@prestashop
class DeliveryCarrierBatchImporter(DelayedBatchImporter):
    """ Import the PrestaShop Carriers.
    """
    _model_name = ['prestashop.delivery.carrier']

    def run(self, filters=None, **kwargs):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters=filters)
        _logger.info('search for prestashop carriers %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id, **kwargs)


@job(default_channel='root.prestashop')
def import_carriers(session, backend_id, **kwargs):
    return import_batch(
        session,
        'prestashop.delivery.carrier',
        backend_id,
        priority=5,
        **kwargs
    )
