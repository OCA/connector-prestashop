# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

from osv import osv, fields
from base_external_referentials.decorator import only_for_referential, catch_error_in_report, open_report

class product_product(osv.osv):
    _inherit='product.product'

    @only_for_referential('prestashop')
    @open_report
    def _import_resources(self, *args, **kwargs):
        return super(product_product, self)._import_resources(*args, **kwargs)

    @only_for_referential('prestashop')
    @catch_error_in_report
    def _record_one_external_resource(self, *args, **kwargs):
        return super(product_product, self)._record_one_external_resource(*args, **kwargs)

    def export_inventory(self, cr, uid, external_session, product_ids, context=None):
        """

        :param list product_ids: list of product
        :rtype: __
        :return: __
        """
        level_stock = {}
        for product in self.browse(cr, uid, product_ids, context=context):
            level_stock[product.id] = product.qty_available

        print 'level_stock', level_stock

        return True
        

class product_category(osv.osv):
    _inherit='product.category'
        
    @only_for_referential('prestashop')
    @open_report
    def _export_resources(self, *args, **kwargs):
        return super(product_category, self)._import_resources(*args, **kwargs)

    @only_for_referential('prestashop')
    @catch_error_in_report
    def _transform_and_send_one_resource(self, *args, **kwargs):
        return super(product_category, self)._transform_and_send_one_resource(*args, **kwargs)

