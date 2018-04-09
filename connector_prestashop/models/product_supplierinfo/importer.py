# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.addons.queue_job.exception import FailedJobError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from ...components.backend_adapter import PrestaShopCRUDAdapter
from ...components.importer import (
    import_batch,
)
from ...backend import prestashop

import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


@prestashop
class SupplierMapper(Component):
    _name = 'prestashop.supplier.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.supplier'

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
        supplier_image_adapter = self.component(
            usage='prestashop.adapter', model_name='prestashop.supplier.image'
        )
        try:
            return {'image': supplier_image_adapter.read(record['id'])}
        except:
            return {}


@prestashop
class SupplierImporter(Component):
    """ Import one simple record """
    _name = 'prestashop.supplier.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.supplier'

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
class SupplierBatchImporter(Component):
    _name = 'prestashop.supplier.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = 'prestashop.supplier'


@prestashop
class SupplierInfoMapper(Component):
    _name = 'prestashop.product.supplierinfo.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.supplierinfo'

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
class SupplierInfoImporter(Component):
    _name = 'prestashop.product.supplierinfo.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.product.supplierinfo'

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
class SupplierInfoBatchImporter(Component):
    _name = 'prestashop.product.supplierinfo.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = 'prestashop.product.supplierinfo'
