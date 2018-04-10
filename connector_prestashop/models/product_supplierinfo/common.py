# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields

from ...components.backend_adapter import (
    PrestaShopCRUDAdapter,
    PrestaShopWebServiceImage,
    GenericAdapter,
)
from ...backend import prestashop


class ResPartner(models.Model):
    _inherit = 'res.partner'

    prestashop_supplier_bind_ids = fields.One2many(
        comodel_name='prestashop.supplier',
        inverse_name='odoo_id',
        string="PrestaShop supplier bindings",
    )


class PrestashopSupplier(models.Model):
    _name = 'prestashop.supplier'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'res.partner': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.supplierinfo',
        inverse_name='odoo_id',
        string="PrestaShop bindings",
    )


class PrestashopProductSupplierinfo(models.Model):
    _name = 'prestashop.product.supplierinfo'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.supplierinfo': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.supplierinfo',
        string='Supplier info',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
    ]


@prestashop
class SupplierImageAdapter(PrestaShopCRUDAdapter):
    _name = 'prestashop.supplier.image.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.supplier.image'

    _prestashop_image_model = 'suppliers'

    def read(self, supplier_id, options=None):
        client = PrestaShopWebServiceImage(self.prestashop.api_url,
                                           self.prestashop.webservice_key)
        res = client.get_image(
            self._prestashop_image_model,
            supplier_id,
            options=options
        )
        return res['content']


class SupplierAdapter(Component):
    _name = 'prestashop.supplier.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.supplier'
    
    _prestashop_model = 'suppliers'


class SupplierInfoAdapter(Component):
    _name = 'prestashop.product.supplierinfo.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.supplierinfo'

    
    _prestashop_model = 'product_suppliers'
