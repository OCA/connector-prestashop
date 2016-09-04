# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def update_prestashop_quantities(self):
        for move in self:
            move.product_id.update_prestashop_qty()

    @api.model
    def get_stock_locations(self):
        warehouses = self.env['stock.warehouse'].search([])
        locations = warehouses.mapped('lot_stock_id.child_ids').filtered(
            lambda x: x.usage == 'internal') + warehouses.mapped(
            'lot_stock_id')
        return locations

    @api.model
    def create(self, vals):
        stock_move = super(StockMove, self).create(vals)
        locations = self.get_stock_locations()
        if vals['location_id'] in locations.ids:
            stock_move.update_prestashop_quantities()
        return stock_move

    @api.multi
    def action_cancel(self):
        res = super(StockMove, self).action_cancel()
        locations = self.get_stock_locations()
        for move in self:
            if move.location_id.id in locations.ids:
                move.update_prestashop_quantities()
        return res

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        locations = self.get_stock_locations()
        for move in self:
            if move.location_dest_id.id in locations.ids:
                move.update_prestashop_quantities()
        return res
