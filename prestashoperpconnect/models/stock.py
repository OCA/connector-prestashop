# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright 2013 Camptocamp SA
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    @author: Guewen Baconnier
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv.orm import Model


class StockMove(Model):
    _inherit = 'stock.move'

    def update_prestashop_quantities(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            move.product_id.update_prestashop_quantities()

    def get_stock_location_ids(self, cr, uid, context=None):
        warehouse_obj = self.pool['stock.warehouse']
        warehouse_ids = warehouse_obj.search(cr, uid, [], context=context)
        warehouses = warehouse_obj.browse(
            cr, uid, warehouse_ids, context=context
        )
        location_ids = []
        for warehouse in warehouses:
            location_ids.append(warehouse.lot_stock_id.id)
        return location_ids

    def create(self, cr, uid, vals, context=None):
        stock_id = super(StockMove, self).create(
            cr, uid, vals, context=context
        )
        location_ids = self.get_stock_location_ids(cr, uid, context=context)
        if vals['location_id'] in location_ids:
            self.update_prestashop_quantities(
                cr, uid, [stock_id], context=context
            )
        return stock_id

    def action_cancel(self, cr, uid, ids, context=None):
        res = super(StockMove, self).action_cancel(
            cr, uid, ids, context=context
        )
        location_ids = self.get_stock_location_ids(cr, uid, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            if move.location_id.id in location_ids:
                self.update_prestashop_quantities(
                    cr, uid, [move.id], context=context
                )
        return res

    def action_done(self, cr, uid, ids, context=None):
        res = super(StockMove, self).action_done(cr, uid, ids, context=context)
        location_ids = self.get_stock_location_ids(cr, uid, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            if move.location_dest_id.id in location_ids:
                self.update_prestashop_quantities(
                    cr, uid, [move.id], context=context
                )
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
