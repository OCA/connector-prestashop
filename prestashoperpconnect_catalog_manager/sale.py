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

class sale_shop(osv.osv):
    _inherit = 'sale.shop'

    def get_shop_lang_to_export(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        lang_code = []
        shop_data = self.browse(cr, uid, ids)
        for shop in shop_data:
            lang_code = [x.code for x in shop.referential_id.exportable_lang_ids]
        return lang_code

    def export_catalog_prestashop(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        context['lang_to_export'] = self.get_shop_lang_to_export(cr, uid, ids, context=context)
        #self.export_resources(cr, uid, ids, 'product.category', context=context)
        self.export_resources(cr, uid, ids, 'product.product', context=context)
        #TODO update the last date
        return True

    def _prepare_attribute_shop_fields(self, cr, uid, context=None):
        res = super(sale_shop, self)._prepare_attribute_shop_fields(cr, uid, context=context)
        #TODO improve this code, maybe the best will be to pass more information (all attribut information)
        #so we can create more custom field, like selection, and we can customise the name
        prestashop_fields = {
                    'meta_title': 'char',
                    'meta_description': 'char',
                    'meta_keywords': 'char',
                    'link_rewrite': 'char',
                    'tags': 'char',
                    'short_description': 'text',
                    'available_for_order': 'boolean',
                    'show_price': 'boolean',
                    'online_only': 'boolean',
                    }
        res.update(prestashop_fields)
        return res

    def generate_shop_attributes(self, cr, uid, ids, context=None):
        context['dont_add_referentials'] = True
        return super(sale_shop, self).generate_shop_attributes(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
