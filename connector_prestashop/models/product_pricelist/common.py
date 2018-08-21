# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    prestashop_groups_bind_ids = fields.One2many(
        comodel_name='prestashop.groups.pricelist',
        inverse_name='openerp_id',
        string='PrestaShop user groups',
    )


class PrestashopGroupsPricelist(models.Model):
    _name = 'prestashop.groups.pricelist'
    _inherit = 'prestashop.binding'
    _inherits = {'product.pricelist': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='product.pricelist',
        required=True,
        ondelete='cascade',
        string='Openerp Pricelist',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
    ]


class PricelistAdapter(Component):
    _name = 'prestashop.groups.pricelist.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.groups.pricelist'
    _prestashop_model = 'groups'
