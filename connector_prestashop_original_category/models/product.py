# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if 'prestashop_default_category_id' in vals:
            res.categ_id = vals.get('prestashop_default_category_id') or \
                self._get_default_category_id()
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if 'prestashop_default_category_id' in vals:
            self.categ_id = vals.get('prestashop_default_category_id') or \
                self._get_default_category_id()
        return res
