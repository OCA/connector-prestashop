# -*- coding: utf-8 -*-
# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models

from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.backend_adapter import (
    GenericAdapter)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    prestashop_specific_price_bind_ids = fields.One2many(
        comodel_name='prestashop.specific.price',
        inverse_name='odoo_id',
        string='PrestaShop Specific Price',
    )


class PrestashopSpecificPrice(models.Model):
    _name = 'prestashop.specific.price'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.pricelist.item': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        required=True,
        ondelete='cascade',
        string='Odoo Pricelist',
        oldname='openerp_id',
    )


@prestashop
class PricelistSpecificPriceAdapter(GenericAdapter):
    _model_name = 'prestashop.specific.price'
    _prestashop_model = 'specific_prices'
    _export_node_name = 'specific_price'
