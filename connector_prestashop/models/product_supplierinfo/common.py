# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields

from odoo.addons.component.core import Component
from ...components.backend_adapter import (
    PrestaShopWebServiceImage,
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

    def import_suppliers(self, backend, since_date, **kwargs):
        filters = None
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
        now_fmt = fields.Datetime.now()
        self.env['prestashop.supplier'].with_delay().import_batch(
            backend,
            filters,
            **kwargs
        )
        self.env['prestashop.product.supplierinfo'].with_delay().import_batch(
            backend,
            **kwargs
        )
        backend.import_suppliers_since = now_fmt
        return True


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


@prestashop
class SupplierImageAdapter(Component):
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


@prestashop
class SupplierAdapter(Component):
    _name = 'prestashop.supplier.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.supplier'
    _prestashop_model = 'suppliers'


@prestashop
class SupplierInfoAdapter(Component):
    _name = 'prestashop.product.supplierinfo.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.supplierinfo'
    _prestashop_model = 'product_suppliers'
