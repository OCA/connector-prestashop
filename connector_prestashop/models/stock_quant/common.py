# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


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
            res = super(StockQuant, self).write(vals)
            if (location | quant.location_id) & ps_locations:
                quant.invalidate_cache()
                quant.product_id.update_prestashop_qty()
        return res

    @api.multi
    def unlink(self):
        ps_locations = self.env['stock.location'].\
            get_prestashop_stock_locations()
        self.filtered(lambda x: x.location_id in ps_locations).mapped(
            'product_id').update_prestashop_qty()
        return super(StockQuant, self).unlink()
