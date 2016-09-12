# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.shop',
        inverse_name='openerp_id',
        readonly=True,
        string='PrestaShop Bindings',
    )


class PrestashopShop(models.Model):
    _name = 'prestashop.shop'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Shop'

    @api.multi
    @api.depends('shop_group_id', 'shop_group_id.backend_id')
    def _compute_backend_id(self):
        self.backend_id = self.shop_group_id.backend_id.id

    name = fields.Char(
        string='Name',
        help="The name of the method on the backend",
        required=True
    )
    shop_group_id = fields.Many2one(
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
        required=True,
        ondelete='cascade',
    )
    openerp_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='WareHouse',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    # what is the exact purpose of this field?
    default_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Default Product Category',
        help="The category set on products when?? TODO."
        "\nOpenERP requires a main category on products for accounting."
    )
    backend_id = fields.Many2one(
        compute='_compute_backend_id',
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        store=True,
    )
    default_url = fields.Char('Default url')


@prestashop
class ShopAdapter(GenericAdapter):
    _model_name = 'prestashop.shop'
    _prestashop_model = 'shops'
