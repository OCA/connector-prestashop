# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes

from openerp.addons.connector.queue.job import job

from ...backend import prestashop
from ...unit.importer import PrestashopImporter
from openerp.addons.connector.unit.mapper import ImportMapper, mapping
from ...connector import get_environment

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug('Can not `from prestapyt import PrestaShopWebServiceError`.')


@prestashop
class ProductImageMapper(ImportMapper):
    _model_name = 'prestashop.product.image'

    direct = [
        # ('content', 'file_db_store'),
    ]

    @mapping
    def owner_id(self, record):
        return {
            'owner_id': self.binder_for(
                'prestashop.product.template').to_odoo(
                record['id_product'], unwrap=True).id
        }

    @mapping
    def name(self, record):
        product = self.binder_for('prestashop.product.template').to_odoo(
            record['id_product'], unwrap=True)
        return {'name': '%s_%s' % (product.name, record['id_image'])}

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
class ProductImageImport(PrestashopImporter):
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
            super(ProductImageImport, self).run(image_id)
        except PrestaShopWebServiceError:
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
