# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from contextlib import contextmanager

from odoo import models, fields, api, exceptions, _

from odoo.addons.connector.connector import ConnectorEnvironment
from ...components.importer import import_batch, import_record
# from ...components.auto_matching_importer import AutoMatchingImporter
from ...components.backend_adapter import  api_handle_errors
from ...components.version_key import VersionKey


from ..product_template.importer import import_inventory
from ..product_supplierinfo.importer import import_suppliers
from ..account_invoice.importer import import_refunds
from ..sale_order.importer import import_orders_since


_logger = logging.getLogger(__name__)


class PrestashopShopGroup(models.Model):
    _name = 'prestashop.shop.group'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Shop Group'

    name = fields.Char('Name', required=True)
    shop_ids = fields.One2many(
        comodel_name='prestashop.shop',
        inverse_name='shop_group_id',
        readonly=True,
        string="Shops",
    )
    company_id = fields.Many2one(
        related='backend_id.company_id',
        comodel_name="res.company",
        string='Company'
    )



class ShopGroupAdapter(Component):
    _name = 'prestashop.shop.group.adapter'
    _inherit = 'prestashop.adapter'
#     _model_name = 'prestashop.shop.group'
    _apply_on = 'prestashop.shop.group'
    _prestashop_model = 'shop_groups'
