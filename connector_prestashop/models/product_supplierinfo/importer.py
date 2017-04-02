# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime
from openerp.addons.connector.exception import NothingToDoJob

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import ImportMapper, mapping

from ...backend import prestashop
from ...unit.importer import (
    DelayedBatchImporter,
    PrestashopImporter,
    import_batch,
)
from ...unit.backend_adapter import PrestaShopCRUDAdapter
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug('Can not `from prestapyt import PrestaShopWebServiceError`.')


@prestashop
class SupplierMapper(ImportMapper):
    _model_name = 'prestashop.supplier'

    direct = [
        ('name', 'name'),
        ('id', 'prestashop_id'),
        ('active', 'active'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def supplier(self, record):
        return {
            'supplier': True,
            'is_company': True,
            'customer': False,
        }

    @mapping
    def image(self, record):
        supplier_image_adapter = self.unit_for(
            PrestaShopCRUDAdapter, 'prestashop.supplier.image'
        )
        try:
            return {'image': supplier_image_adapter.read(record['id'])}
        except:
            return {}


@prestashop
class SupplierRecordImport(PrestashopImporter):
    """ Import one simple record """
    _model_name = 'prestashop.supplier'

    def _create(self, record):
        try:
            return super(SupplierRecordImport, self)._create(record)
        except ZeroDivisionError:
            del record['image']
            return super(SupplierRecordImport, self)._create(record)

    def _after_import(self, erp_id):
        binder = self.binder_for(self._model_name)
        ps_id = binder.to_backend(erp_id)
        import_batch(
            self.session,
            'prestashop.product.supplierinfo',
            self.backend_record.id,
            filters={'filter[id_supplier]': '%d' % ps_id},
            priority=10,
        )


@prestashop
class SupplierBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.supplier'


@prestashop
class SupplierInfoMapper(ImportMapper):
    _model_name = 'prestashop.product.supplierinfo'

    direct = [
        ('product_supplier_reference', 'product_code'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def name(self, record):
        binder = self.binder_for('prestashop.supplier')
        partner = binder.to_odoo(record['id_supplier'], unwrap=True)
        return {'name': partner.id}

    @mapping
    def product_id(self, record):
        binder = self.binder_for('prestashop.product.combination')
        if record['id_product_attribute'] != '0':
            return {'product_id': binder.to_odoo(
                record['id_product_attribute'], unwrap=True).id}
        return {
            'product_id': binder.to_odoo(record['id_product'], unwrap=True).id,
        }

    @mapping
    def product_tmpl_id(self, record):
        binder = self.binder_for('prestashop.product.template')
        erp_id = binder.to_odoo(record['id_product'], unwrap=True)
        return {'product_tmpl_id': erp_id.id}

    @mapping
    def required(self, record):
        return {'min_qty': 0.0, 'delay': 1}


@prestashop
class SupplierInfoImport(PrestashopImporter):
    _model_name = 'prestashop.product.supplierinfo'

    def _import_dependencies(self):
        record = self.prestashop_record
        try:
            self._import_dependency(
                record['id_supplier'], 'prestashop.supplier'
            )
            self._import_dependency(
                record['id_product'], 'prestashop.product.template'
            )

            if record['id_product_attribute'] != '0':
                self._import_dependency(
                    record['id_product_attribute'],
                    'prestashop.product.combination'
                )
        except PrestaShopWebServiceError:
            raise NothingToDoJob('Error fetching a dependency')


@prestashop
class SupplierInfoBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.product.supplierinfo'


@job(default_channel='root.prestashop')
def import_suppliers(session, backend_id, since_date):
    filters = None
    if since_date:
        filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    import_batch(session, 'prestashop.supplier', backend_id, filters)
    import_batch(session, 'prestashop.product.supplierinfo', backend_id)
    session.env['prestashop.backend'].browse(backend_id).write({
        'import_suppliers_since': now_fmt
    })
