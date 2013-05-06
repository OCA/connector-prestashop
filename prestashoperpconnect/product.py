# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2013 Akretion                                               #
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

from openerp.osv import fields, orm


class product_category(orm.Model):
    _inherit = 'product.category'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.res.partner',
            'openerp_id',
            string="PrestaShop Bindings"
        ),
    }


class prestashop_product_category(orm.Model):
    _name = 'prestashop.product.category'
    _inherit = 'prestashop.binding'
    _inherits = {'product.category': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.category',
            string='Product Category',
            required=True,
            ondelete='cascade'
        ),
        'default_shop_id': fields.many2one('prestashop.shop'),
        'date_add': fields.datetime(
            'Created At (on PrestaShop)',
            readonly=True
        ),
        'date_upd': fields.datetime(
            'Updated At (on PrestaShop)',
            readonly=True
        ),
        'description': fields.char('Description', translate=True),
        'link_rewrite': fields.char('Friendly URL', translate=True),
        'meta_description': fields.char('Meta description', translate=True),
        'meta_keywords': fields.char('Meta keywords', translate=True),
        'meta_title': fields.char('Meta title', translate=True),
    }


class product_product(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.product',
            'openerp_id',
            string='PrestaShop Bindings'
        ),
    }


class prestashop_product_product(orm.Model):
    _name = 'prestashop.product.product'
    _inherit = 'prestashop.binding'
    _inherits = {'product.product': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.product',
            string='Product',
            required=True,
            ondelete='cascade'
        ),
        #TODO FIXME what name give to field present in prestashop_product_product and product_product
        'active_conn': fields.boolean(
            'Active',
            help='if check, this object is always available'),
        'sale_ok': fields.boolean(
            'For sale',
            help='see parent field'
        ),
        'description_html': fields.html(
            'Description',
            #type='html',
            help="Description html from prestashop"
        ),
        'date_add': fields.datetime(
            'Created At (on Presta)',
            readonly=True
        ),
        'date_upd': fields.datetime(
            'Updated At (on Presta)',
            readonly=True
        ),
    }

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         "A product with the same ID on Prestashop already exists")
    ]

class product_image(orm.Model):
    _inherit = 'product.images'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.image',
            'openerp_id',
            string='PrestaShop Bindings'
        ),
    }


class prestashop_product_image(orm.Model):
    _name = 'prestashop.product.image'
    _inherit = 'prestashop.binding'
    _inherits = {'product.images': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.images',
            string='Product image',
            required=True,
            ondelete='cascade'
        )
    }
