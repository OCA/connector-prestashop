from openerp.osv.orm import Model


class StockPicking(Model):
    _inherit = 'stock.picking'

    def action_done(self, cr, uid, ids, context=None):
        res = super(StockPicking, self).action_done(
            cr, uid, ids, context=context
        )
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.type == 'in':
                self._update_prestashop_quantities(
                    cr, uid, ids, context=context
                )
        return res

    def _update_prestashop_quantities(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context=context):
            for move in picking.move_lines:
                move._update_prestashop_quantities()

    def action_cancel(self, cr, uid, ids, context=None):
        res = super(StockPicking, self).action_cancel(
            cr, uid, ids, context=context
        )
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.type == 'out':
                self._update_prestashop_quantities(
                    cr, uid, ids, context=context
                )
        return res


class StockMove(Model):
    _inherit = 'stock.move'

    def _update_prestashop_quantities(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            move.product_id._update_prestashop_quantities()


class StockPickingOut(Model):
    _inherit = 'stock.picking.out'

    def create(self, cr, uid, vals, context=None):
        picking_out_id = super(StockPickingOut, self).create(
            cr, uid, vals, context=context
        )
        self._update_prestashop_quantities(
            cr, uid, [picking_out_id], context=context
        )
        return picking_out_id

    def _update_prestashop_quantities(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        return picking_obj._update_prestashop_quantities(
            cr, uid, ids, context=context
        )
