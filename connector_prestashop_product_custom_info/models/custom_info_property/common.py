# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.component.core import Component


class CustomInfoProperty(models.Model):
    _inherit = 'custom.info.property'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.feature',
        inverse_name='odoo_id',
        string="PrestaShop Bindings",
    )


class PrestashopProductFeature(models.Model):
    _name = 'prestashop.product.feature'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'custom.info.property': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='custom.info.property',
        required=True,
        ondelete='cascade',
        string='Custom Information Property',
    )


class ProductFeatureBinder(Component):
    _name = 'prestashop.product.feature.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.product.feature'


class ProductFeatureAdapter(Component):
    _name = 'prestashop.product.feature.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.feature'
    _prestashop_model = 'product_features'
    _export_node_name = 'product_feature'
