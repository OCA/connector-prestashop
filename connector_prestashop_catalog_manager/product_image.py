# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os.path
from openerp.addons.connector.event import on_record_write, on_record_unlink
from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.connector_prestashop.unit.binder import PrestashopBinder
from openerp.addons.connector_prestashop.unit.exporter import (
    PrestashopExporter,
    export_record)
from openerp.addons.connector_prestashop.unit.deleter import (
    export_delete_record
)

from openerp.addons.connector_prestashop.unit.mapper import (
    PrestashopExportMapper
)

from openerp.addons.connector_prestashop.connector import get_environment
from openerp.addons.connector_prestashop.backend import prestashop

import os
from openerp import models, fields
from openerp.tools.translate import _


@on_record_write(model_names='base_multi_image.image')
def product_image_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.image',
                            binding.id, record.file_db_store,
                            priority=20)


@on_record_unlink(model_names='base_multi_image.image')
def product_image_unlink(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.prestashop_bind_ids:
        product = session.env[record.owner_model].browse(record.owner_id)
        if product.exists():
            product_template = product.prestashop_bind_ids.filtered(
                lambda x: x.backend_id == binding.backend_id)
            if product_template:
                env_product = get_environment(
                    session, 'prestashop.product.template',
                    binding.backend_id.id)
                binder_product = env_product.get_connector_unit(
                    PrestashopBinder)
                external_product_id = binder_product.to_backend(
                    product_template.id)
                env = get_environment(
                    session, binding._name, binding.backend_id.id)
                binder = env.get_connector_unit(PrestashopBinder)
                external_id = binder.to_backend(binding.id)
                resource = 'images/products/%s' % (external_product_id)
                if external_id:
                    export_delete_record.delay(
                        session, binding._name, binding.backend_id.id,
                        external_id, resource)


class ProductImage(models.Model):
    _inherit = 'base_multi_image.image'

    front_image = fields.Boolean(string='Front image')


@prestashop
class ProductImageExport(PrestashopExporter):
    _model_name = 'prestashop.product.image'

    def _create(self, record):
        res = super(ProductImageExport, self)._create(record)
        return res['prestashop']['image']['id']

    def _update(self, record):
        res = super(ProductImageExport, self)._update(record)
        return res['prestashop']['image']['id']

    def _run(self, fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.erp_record

        if self._has_to_skip():
            return

        # export the missing linked resources
        self._export_dependencies()
        map_record = self.mapper.map_record(self.erp_record)

        if self.prestashop_id:
            record = map_record.values()
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self.prestashop_id = self._update(record)
        else:
            record = map_record.values(for_create=True)
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self.prestashop_id = self._create(record)
            self._after_export()
        message = _('Record exported with ID %s on Prestashop.')
        return message % self.prestashop_id


@prestashop
class ProductImageExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.product.image'

    direct = [
        ('name', 'name'),
    ]

    def _get_file_name(self, record):
        """
        Get file name with extension from depending storage.
        :param record: browse record
        :return: string: file name.extension.
        """
        file_name = record.odoo_id.filename
        if not file_name:
            storage = record.odoo_id.storage
            if storage == 'url':
                file_name = os.path.splitext(
                    os.path.basename(record.odoo_id.url))
            elif storage == 'db':
                if not record.odoo_id.filename:
                    file_name = '%s_%s.jpg' % (
                        record.odoo_id.owner_model,
                        record.odoo_id.owner_id)
                file_name = os.path.splitext(
                    os.path.basename(record.odoo_id.filename or file_name))
            elif storage == 'file':
                file_name = os.path.splitext(
                    os.path.basename(record.odoo_id.path))
        return file_name

    @mapping
    def source_image(self, record):
        content = getattr(
            record.odoo_id, "_get_image_from_%s" % record.odoo_id.storage)()
        return {'content': content}

    @mapping
    def product_id(self, record):
        if record.odoo_id.owner_model == u'product.product':
            product_tmpl_id = record.env['product.product'].browse(
                record.odoo_id.owner_id).product_tmpl_id.id
        else:
            product_tmpl_id = record.odoo_id.owner_id
        return {'id_product': product_tmpl_id}

    @mapping
    def extension(self, record):
        return {'extension': self._get_file_name(record)[1]}

    @mapping
    def legend(self, record):
        return {'legend': record.name}

    @mapping
    def filename(self, record):
        file_name = record.filename
        if not file_name:
            file_name = '.'.join(self._get_file_name(record))
        return {'filename': file_name}
