# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector_prestashop.unit.exporter import \
    PrestashopExporter
from openerp.addons.connector_prestashop.unit.mapper import (
    PrestashopExportMapper
)
from openerp.addons.connector_prestashop.unit.backend_adapter import (
    PrestaShopWebServiceImage
)
from openerp.addons.connector_prestashop.backend import prestashop

from openerp import models, fields
from openerp.tools.translate import _

import os
import os.path


class ProductImage(models.Model):
    _inherit = 'base_multi_image.image'

    front_image = fields.Boolean(string='Front image')


@prestashop
class ProductImageExport(PrestashopExporter):
    _model_name = 'prestashop.product.image'

    def _run(self, fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.binding

        if self._has_to_skip():
            return

        # export the missing linked resources
        self._export_dependencies()
        map_record = self.mapper.map_record(self.binding)

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
        self._link_image_to_url()
        message = _('Record exported with ID %s on Prestashop.')
        return message % self.prestashop_id

    def _link_image_to_url(self):
        """Change image storage to a url linked to product prestashop image"""
        api = PrestaShopWebServiceImage(
            api_url=self.backend_record.location,
            api_key=self.backend_record.webservice_key)
        full_public_url = api.get_image_public_url({
            'id_image': str(self.prestashop_id),
            'type': 'image/jpeg',
        })
        if self.binding.url != full_public_url:
            self.binding.with_context(connector_no_export=True).write({
                'url': full_public_url,
                'file_db_store': False,
                'storage': 'url',
            })


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
            product_tmpl = record.env['product.product'].browse(
                record.odoo_id.owner_id).product_tmpl_id
        else:
            product_tmpl = record.env['product.template'].browse(
                record.odoo_id.owner_id)
        binder = self.binder_for('prestashop.product.template')
        ps_product_id = binder.to_backend(product_tmpl, wrap=True)
        return {'id_product': ps_product_id}

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
