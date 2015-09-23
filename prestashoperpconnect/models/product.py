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

from openerp.addons.connector.session import ConnectorSession

from ..unit.import_synchronizer import import_record


class product_category(orm.Model):
    _inherit = 'product.category'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.category',
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
        'active': fields.boolean('Active'),
        'position': fields.integer('Position')
    }

    _defaults = {
        'active': True
    }


class product_image(orm.Model):
    _inherit = 'product.image'

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
    _inherits = {'product.image': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.image',
            string='Product image',
            required=True,
            ondelete='cascade'
        )
    }


class product_template(orm.Model):
    _inherit = 'product.template'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.template',
            'openerp_id',
            string='PrestaShop Bindings'
        ),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['prestashop_bind_ids'] = []
        return super(product_template, self).copy(
            cr, uid, id, default=default, context=context
        )

    def update_prestashop_quantities(self, cr, uid, ids, context=None):
        for template in self.browse(cr, uid, ids, context=context):
            for prestashop_template in template.prestashop_bind_ids:
                prestashop_template.recompute_prestashop_qty()
            prestashop_combinations = template.product_variant_ids
            for prestashop_combination in prestashop_combinations:
                prestashop_combination.recompute_prestashop_qty()
        return True


class prestashop_product_template(orm.Model):
    _name = 'prestashop.product.template'
    _inherit = 'prestashop.binding'
    _inherits = {'product.template': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.template',
            string='Template',
            required=True,
            ondelete='cascade'
        ),
        # TODO FIXME what name give to field present in
        # prestashop_product_product and product_product
        'always_available': fields.boolean(
            'Active',
            help='if check, this object is always available'),
        'quantity': fields.float(
            'Computed Quantity',
            help="Last computed quantity to send on Prestashop."
        ),
        'description_html': fields.html(
            'Description',
            translate=True,
            help="Description html from prestashop",
        ),
        'description_short_html': fields.html(
            'Short Description',
            translate=True,
        ),
        'date_add': fields.datetime(
            'Created At (on Presta)',
            readonly=True
        ),
        'date_upd': fields.datetime(
            'Updated At (on Presta)',
            readonly=True
        ),
        'default_shop_id': fields.many2one(
            'prestashop.shop',
            'Default shop',
            required=True
        ),
        'link_rewrite': fields.char(
            'Friendly URL',
            translate=True,
            required=False,
        ),
        'available_for_order': fields.boolean(
            'Available For Order'
        ),
        'show_price': fields.boolean(
            'Show Price'
        ),
        'combinations_ids': fields.one2many(
            'prestashop.product.combination',
            'main_template_id',
            string='Combinations'
        ),
        'reference': fields.char('Original reference'),
    }

    _defaults = {
        'available_for_order': True,
        'show_price': True,
        'always_available': True
    }

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         "A product with the same ID on Prestashop already exists")
    ]

    def recompute_prestashop_qty(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]

        for product in self.browse(cr, uid, ids, context=context):
            new_qty = self._prestashop_qty(cr, uid, product, context=context)
            self.write(
                cr, uid, product.id,
                {'quantity': new_qty},
                context=context
            )
        return True

    def _prestashop_qty(self, cr, uid, product, context=None):
        if context is None:
            context = {}
        backend = product.backend_id
        stock = backend.warehouse_id.lot_stock_id
        stock_field = 'qty_available'
        location_ctx = context.copy()
        location_ctx['location'] = stock.id
        product_stk = self.read(
            cr, uid, product.id, [stock_field], context=location_ctx
        )
        return product_stk[stock_field]


class product_product(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.combination',
            'openerp_id',
            string='PrestaShop Bindings'
        ),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['prestashop_bind_ids'] = []
        return super(product_product, self).copy(
            cr, uid, id, default=default, context=context
        )

    def update_prestashop_quantities(self, cr, uid, ids, context=None):
        for product in self.browse(cr, uid, ids, context=context):
            product_template = product.product_tmpl_id
            prestashop_combinations = (
                len(product_template.product_variant_ids) > 1
                and product_template.product_variant_ids) or []
            if not prestashop_combinations:
                for prestashop_product in product_template.prestashop_bind_ids:
                    prestashop_product.recompute_prestashop_qty()
            else:
                for prestashop_combination in prestashop_combinations:
                    for combination_binding in \
                            prestashop_combination.prestashop_bind_ids:
                        combination_binding.recompute_prestashop_qty()
        return True


class product_pricelist(orm.Model):
    _inherit = 'product.pricelist'

    _columns = {
        'prestashop_groups_bind_ids': fields.one2many(
            'prestashop.groups.pricelist',
            'openerp_id',
            string='Prestashop user groups'
        ),
    }


class prestashop_groups_pricelist(orm.Model):
    _name = 'prestashop.groups.pricelist'
    _inherit = 'prestashop.binding'
    _inherits = {'product.pricelist': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.pricelist',
            string='Openerp Pricelist',
            required=True,
            ondelete='cascade'
        ),
    }
