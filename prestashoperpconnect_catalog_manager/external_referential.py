# -*- encoding: utf-8 -*-
###############################################################################
#
#   Prestashop_catalog_manager for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>. All Rights Reserved
#   @author : Sébastien BEAU <sebastien.beau@akretion.com>
#             Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from osv import osv, fields

class external_referential(osv.osv):
    _inherit = "external.referential"

    _columns = {
        'product_attribute_ids': fields.many2many('product.attribute', 'ext_product_attributes', 'referential_id', 'attribute_id', 'Product Attributes'),
    }

    def export_product_attributes(self, cr, uid, ids, context=None):
        self.export_resources(cr, uid, ids, 'product.attribute', context=context)
        return True
