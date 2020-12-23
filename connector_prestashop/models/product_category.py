# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.category',
        inverse_name='odoo_id',
        string="PrestaShop Bindings",
    )


class PrestashopProductCategory(models.Model):
    _name = 'prestashop.product.category'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.category': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.category',
        required=True,
        ondelete='cascade',
        string='Product Category',
        oldname='openerp_id',
    )
    default_shop_id = fields.Many2one(comodel_name='prestashop.shop')
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True
    )
    description = fields.Char(string='Description', translate=True)
    link_rewrite = fields.Char(string='Friendly URL', translate=True)
    meta_description = fields.Char('Meta description', translate=True)
    meta_keywords = fields.Char(string='Meta keywords', translate=True)
    meta_title = fields.Char(string='Meta title', translate=True)
    active = fields.Boolean(string='Active', default=True)
    position = fields.Integer(string='Position')
