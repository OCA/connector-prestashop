# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if res:
            Location = self.env['stock.location']
            ps_locations = Location.get_prestashop_stock_locations()
            products = self.filtered(
                lambda x: (x.location_id | x.location_dest_id) &
                ps_locations).mapped('product_id')
            # outgoing_qty is calculated and still has incorrect value in cache
            self.invalidate_cache()
            products.update_prestashop_qty()
        return res
