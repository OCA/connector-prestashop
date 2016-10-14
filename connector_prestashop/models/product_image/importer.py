# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper)

from ...backend import prestashop
from ...connector import get_environment
from ...unit.importer import PrestashopImporter

import mimetypes
import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


@prestashop
class ProductImageMapper(ImportMapper):
    _model_name = 'prestashop.product.image'

    direct = [
        # ('content', 'file_db_store'),
    ]

    @mapping
    def from_template(self, record):
        binder = self.binder_for('prestashop.product.template')
        template = binder.to_odoo(record['id_product'], unwrap=True)
        name = '%s_%s' % (template.name, record['id_image'])
        return {'owner_id': template.id, 'name': name}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def extension(self, record):
        return {'extension': mimetypes.guess_extension(record['type'])}

    @mapping
    def image_url(self, record):
        url = self.backend_record.location.encode()
        url += '/img/p/' + '/'.join(list(record['id_image']))
        extension = ''
        if record['type'] == 'image/jpeg':
            extension = '.jpg'
        url += '/' + record['id_image'] + extension
        return {'url': url}
        # return {'storage': 'db'}

    @mapping
    def filename(self, record):
        return {'filename': '%s.jpg' % record['id_image']}

    @mapping
    def storage(self, record):
        return {'storage': 'url'}
        # return {'storage': 'db'}

    @mapping
    def owner_model(self, record):
        return {'owner_model': 'product.template'}


@prestashop
class ProductImageImporter(PrestashopImporter):
    _model_name = [
        'prestashop.product.image',
    ]

    def _get_prestashop_data(self):
        """ Return the raw PrestaShop data for ``self.prestashop_id`` """
        return self.backend_adapter.read(self.template_id, self.image_id)

    def run(self, template_id, image_id):
        self.template_id = template_id
        self.image_id = image_id

        try:
            super(ProductImageImporter, self).run(image_id)
        except PrestaShopWebServiceError:
            # TODO Check this silent error
            pass


@job(default_channel='root.prestashop')
def import_product_image(session, model_name, backend_id, product_tmpl_id,
                         image_id):
    """Import a product image"""
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(PrestashopImporter)
    importer.run(product_tmpl_id, image_id)


@job(default_channel='root.prestashop')
def set_product_image_variant(
        session, model_name, backend_id, combination_ids):
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(PrestashopImporter)
    importer.set_variant_images(combination_ids)
