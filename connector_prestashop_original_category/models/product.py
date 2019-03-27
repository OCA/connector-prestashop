# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if 'prestashop_default_category_id' in vals:
            vals.update(
                {'categ_id': vals.get('prestashop_default_category_id')}
            ) if vals.get('prestashop_default_category_id') else vals.update(
                {'categ_id': self._get_default_category_id()})
        res = super(ProductTemplate, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'prestashop_default_category_id' in vals:
            vals.update(
                {'categ_id': vals.get('prestashop_default_category_id')}
            ) if vals.get('prestashop_default_category_id') else vals.update(
                {'categ_id': self._get_default_category_id()})
        res = super(ProductTemplate, self).write(vals)
        return res
