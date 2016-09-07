# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    prestashop_synchronized = fields.Boolean(
        string='Sync with PrestaShop',
        help='Check this option to synchronize this location with PrestaShop')

    @api.model
    def get_prestashop_stock_locations(self):
        prestashop_locations = self.search([
            ('prestashop_synchronized', '=', True),
            ('usage', '=', 'internal'),
        ])
        return prestashop_locations
