# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def create(self, vals):
        location_obj = self.env['stock.location']
        ps_locations = location_obj.get_prestashop_stock_locations()
        quant = super(StockQuant, self).create(vals)
        if quant.location_id in ps_locations:
            quant.product_id.update_prestashop_qty()
        return quant

    @api.multi
    def write(self, vals):
        location_obj = self.env['stock.location']
        ps_locations = location_obj.get_prestashop_stock_locations()
        for quant in self:
            location = quant.location_id
            super(StockQuant, self).write(vals)
            if location in ps_locations:
                quant.invalidate_cache()
                quant.product_id.update_prestashop_qty()
        return True

    @api.multi
    def unlink(self):
        ps_locations = self.env['stock.location'].\
            get_prestashop_stock_locations()
        self.filtered(lambda x: x.location_id in ps_locations).mapped(
            'product_id').update_prestashop_qty()
        return super(StockQuant, self).unlink()
