# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    product_custom_info_template_id = fields.Many2one(
        comodel_name='custom.info.template',
        string='Product Custom Information Template',
        required=True,
        default=lambda self: self._default_product_custom_info_template_id(),
        domain=[('model', '=', 'product.template')],
        help='Default template for imported products. Only features of '
             'products with this template will be updated.',
    )

    product_custom_info_category_id = fields.Many2one(
        comodel_name='custom.info.category',
        string='Product Custom Information Category',
        required=True,
        default=lambda self: self._default_product_custom_info_category_id(),
        help='Default category for imported features. Only values of features '
             'with this category will be updated.'
    )

    @api.model
    def _default_product_custom_info_template_id(self):
        return self.env.ref('connector_prestashop_product_custom_info.'
                            'product_custom_info_template',
                            raise_if_not_found=False)

    @api.model
    def _default_product_custom_info_category_id(self):
        return self.env.ref('connector_prestashop_product_custom_info.'
                            'product_custom_info_category',
                            raise_if_not_found=False)

    @api.multi
    def import_features_and_values(self):
        for backend_record in self:
            self.env['prestashop.product.feature.value'].with_delay(
                priority=5).import_batch(backend_record, priority=5)
            self.env['prestashop.product.feature'].with_delay(
                priority=10).import_batch(backend_record, priority=10)
        return True
