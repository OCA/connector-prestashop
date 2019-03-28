# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.component.core import Component


class CustomInfoOption(models.Model):
    _inherit = 'custom.info.option'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.feature.value',
        inverse_name='odoo_id',
        string="PrestaShop Bindings",
    )


class PrestashopProductFeatureValue(models.Model):
    _name = 'prestashop.product.feature.value'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'custom.info.option': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='custom.info.option',
        required=True,
        ondelete='cascade',
        string='Custom Information Option',
    )

    custom = fields.Boolean('Custom')


class ProductFeatureValueBinder(Component):
    _name = 'prestashop.product.feature.value.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.product.feature.value'


class ProductFeatureValueAdapter(Component):
    _name = 'prestashop.product.feature.value.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.feature.value'
    _prestashop_model = 'product_feature_values'
    _export_node_name = 'product_feature_value'
