# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
from odoo import models, fields
from odoo.addons.component.core import AbstractComponent
from ...components.backend_adapter import PrestaShopWebServiceImage


class ProductImage(models.Model):
    _inherit = 'base_multi_image.image'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.image',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopProductImage(models.Model):
    _name = 'prestashop.product.image'
    _inherit = 'prestashop.binding'
    _inherits = {'base_multi_image.image': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='base_multi_image.image',
        required=True,
        ondelete='cascade',
        string='Product image',
        oldname='openerp_id',
    )


class ProductImageAdapter(AbstractComponent):
    _name = 'prestashop.product.image.adapter'
    _inherit = 'prestashop.crud.adapter'

    _model_name = 'prestashop.product.image'
    _prestashop_image_model = 'products'
    _prestashop_model = '/images/products'
    _export_node_name = '/images/products'
    _export_node_name_res = 'image'

    def read(self, product_tmpl_id, image_id, options=None):
        api = PrestaShopWebServiceImage(self.prestashop.api_url,
                                        self.prestashop.webservice_key)
        return api.get_image(
            self._prestashop_image_model,
            product_tmpl_id,
            image_id,
            options=options
        )

    def create(self, attributes=None):
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        # TODO: odoo logic in the adapter? :-(
        url = '{}/{}'.format(self._prestashop_model, attributes['id_product'])
        return api.add(url, files=[(
            'image',
            attributes['filename'].encode('utf-8'),
            base64.b64decode(attributes['content'])
        )])

    def write(self, id, attributes=None):
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        # TODO: odoo logic in the adapter? :-(
        url = '{}/{}'.format(self._prestashop_model, attributes['id_product'])
        url_del = '{}/{}/{}/{}'.format(
            api._api_url, self._prestashop_model, attributes['id_product'], id)
        try:
            api._execute(url_del, 'DELETE')
        except:
            pass
        return api.add(url, files=[(
            'image',
            attributes['filename'].encode('utf-8'),
            base64.b64decode(attributes['content'])
        )])

    def delete(self, resource, id):
        """ Delete a record on the external system """
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        return api.delete(resource, resource_ids=id)
