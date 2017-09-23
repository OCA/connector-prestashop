# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.addons.queue_job.exception import FailedJobError
from odoo.addons.queue_job.job import job
from odoo.addons.connector.unit.mapper import ImportMapper, mapping

from ...components.backend_adapter import PrestaShopCRUDAdapter
from ...components.importer import (
    PrestashopImporter,
    import_batch,
    DelayedBatchImporter,
)
from ...backend import prestashop

import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


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
class SupplierImporter(PrestashopImporter):
    """ Import one simple record """
    _model_name = 'prestashop.supplier'

    def _create(self, record):
        try:
            return super(SupplierImporter, self)._create(record)
        except ZeroDivisionError:
            del record['image']
            return super(SupplierImporter, self)._create(record)

    def _after_import(self, binding):
        super(SupplierImporter, self)._after_import(binding)
        binder = self.binder_for()
        ps_id = binder.to_external(binding)
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
        partner = binder.to_internal(record['id_supplier'], unwrap=True)
        return {'name': partner.id}

    @mapping
    def product_id(self, record):
        if record['id_product_attribute'] != '0':
            binder = self.binder_for('prestashop.product.combination')
            product = binder.to_internal(
                record['id_product_attribute'],
                unwrap=True,
            )
            return {'product_id': product.id}
        return {}

    @mapping
    def product_tmpl_id(self, record):
        binder = self.binder_for('prestashop.product.template')
        template = binder.to_internal(record['id_product'], unwrap=True)
        return {'product_tmpl_id': template.id}

    @mapping
    def required(self, record):
        return {'min_qty': 0.0, 'delay': 1}


@prestashop
class SupplierInfoImporter(PrestashopImporter):
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
            raise FailedJobError('Error fetching a dependency')


@prestashop
class SupplierInfoBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.product.supplierinfo'


@job(default_channel='root.prestashop')
def import_suppliers(session, backend_id, since_date, **kwargs):
    filters = None
    if since_date:
        filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
    now_fmt = fields.Datetime.now()
    result = import_batch(
        session,
        'prestashop.supplier',
        backend_id,
        filters,
        **kwargs
    ) or ''
    result += import_batch(
        session,
        'prestashop.product.supplierinfo',
        backend_id,
        **kwargs
    ) or ''
    session.env['prestashop.backend'].browse(backend_id).write({
        'import_suppliers_since': now_fmt
    })
    return result
