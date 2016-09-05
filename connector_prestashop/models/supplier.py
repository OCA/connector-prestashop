# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    prestashop_supplier_bind_ids = fields.One2many(
        comodel_name='prestashop.supplier',
        inverse_name='openerp_id',
        string="PrestaShop supplier bindings",
    )


class PrestashopSupplier(models.Model):
    _name = 'prestashop.supplier'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.supplierinfo',
        inverse_name='openerp_id',
        string="PrestaShop bindings",
    )


class PrestashopProductSupplierinfo(models.Model):
    _name = 'prestashop.product.supplierinfo'
    _inherit = 'prestashop.binding'
    _inherits = {'product.supplierinfo': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='product.supplierinfo',
        string='Supplier info',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]
