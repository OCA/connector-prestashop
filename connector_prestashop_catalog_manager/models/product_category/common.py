# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tools import config
from odoo import fields, models
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector_prestashop.components.backend_adapter\
    import PrestaShopWebServiceImage


class ProductCategory(models.Model):
    _inherit = 'product.category'

    prestashop_image_bind_ids = fields.One2many(
        comodel_name='prestashop.categ.image',
        inverse_name='odoo_id',
        copy=False,
        string='PrestaShop Image Bindings',
    )


class PrestashopCategImage(models.Model):
    _name = 'prestashop.categ.image'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.category': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.category',
        string='Product',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )


class PrestashopCategImageModelBinder(Component):
    _name = 'prestashop.categ.image.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.categ.image'


class CategImageAdapter(Component):
    _name = 'prestashop.categ.image.adapter'
    _inherit = 'prestashop.crud.adapter'
    _apply_on = 'prestashop.categ.image'
    _prestashop_image_model = 'categories'

    def connect(self):
        debug = False
        if config['log_level'] == 'debug':
            debug = True
        return PrestaShopWebServiceImage(self.prestashop.api_url,
                                         self.prestashop.webservice_key,
                                         debug=debug)

    def read(self, category_id, image_id, options=None):
        api = self.connect()
        return api.get_image(
            self._prestashop_image_model,
            category_id,
            image_id,
            options=options
        )

    def create(self, attributes=None):
        api = self.connect()
        image_binary = attributes['image']
        img_filename = attributes['name']
        image_url = 'images/%s/%s' % (
            self._prestashop_image_model, str(attributes['categ_id']))
        return api.add(image_url, files=[
            ('image', img_filename, image_binary)])

    def write(self, id, attributes=None):
        api = self.connect()
        image_binary = attributes['image']
        img_filename = attributes['name']
        delete_url = 'images/%s' % (self._prestashop_image_model)
        api.delete(delete_url,  str(attributes['categ_id']))
        image_url = 'images/%s/%s' % (
            self._prestashop_image_model, str(attributes['categ_id']))
        return api.add(image_url, files=[
            ('image', img_filename, image_binary)])


class PrestashopProductCategoryListener(Component):
    _name = 'prestashop.product.category.event.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'prestashop.product.category'

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        """ Called when a record is created """
        record.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    @skip_if(lambda self, record, **kwargs: self.need_to_export(
        record, **kwargs))
    def on_record_write(self, record, fields=None):
        """ Called when a record is written """
        record.with_delay().export_record(fields=fields)


class ProductCategoryListener(Component):
    _name = 'product.category.event.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'product.category'

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """ Called when a record is written """
        for binding in record.prestashop_bind_ids:
            if not self.need_to_export(binding, fields):
                binding.with_delay().export_record(fields=fields)
        if 'image' in fields:
            if record.prestashop_image_bind_ids:
                for image in record.prestashop_image_bind_ids:
                    image.with_delay().export_record(fields=fields)
            else:
                for presta_categ in record.prestashop_bind_ids:
                    image = self.env['prestashop.categ.image'].create({
                        'backend_id': presta_categ.backend_id.id,
                        'odoo_id': record.id
                    })
                    image.with_delay().export_record(fields=fields)
