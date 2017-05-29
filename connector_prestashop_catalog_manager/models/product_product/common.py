# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class PrestashopProductCombination(models.Model):
    _inherit = 'prestashop.product.combination'
    minimal_quantity = fields.Integer(
        string='Minimal Quantity',
        default=1,
        help='Minimal Sale quantity',
    )
