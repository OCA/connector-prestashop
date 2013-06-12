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

import mimetypes
import json

from openerp.osv import fields, orm
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_write
from openerp.addons.connector.unit.synchronizer import (ExportSynchronizer)
from openerp.addons.connector.unit.mapper import mapping

from .unit.backend_adapter import GenericAdapter

from .connector import get_environment
from .unit.mapper import PrestashopImportMapper
from backend import prestashop


##########  product category ##########
@prestashop
class ProductCategoryMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.category'

    direct = [
        ('name', 'name'),
        ('position', 'sequence'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('description', 'description'),
        ('link_rewrite', 'link_rewrite'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('meta_title', 'meta_title'),
        ('id_shop_default', 'default_shop_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        if record['id_parent'] == '0':
            return {}
        return {'parent_id': self.get_openerp_id(
            'prestashop.product.category',
            record['id_parent']
        )}


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


# Product image connector parts
@prestashop
class ProductImageMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.image'

    direct = [
        ('content', 'file_db_store'),
    ]

    @mapping
    def product_id(self, record):
        return {'product_id': self.get_openerp_id(
            'prestashop.product.product',
            record['id_product']
        )}

    @mapping
    def name(self, record):
        return {'name': record['id_product']+'_'+record['id_image']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def extension(self, record):
        return {"extension": mimetypes.guess_extension(record['type'])}


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


########  product  ########
@prestashop
class ProductMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.product'

    direct = [
        ('name', 'name'),
        ('description', 'description_html'),
        ('weight', 'weight'),
        ('wholesale_price', 'standard_price'),
        ('price', 'lst_price'),
        ('reference', 'default_code'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('id_shop_default', 'default_shop_id'),
        ('link_rewrite', 'link_rewrite'),
    ]

    @mapping
    def active(self, record):
        return {'always_available': bool(int(record['active']))}

    @mapping
    def sale_ok(self, record):
        return {'sale_ok': record['available_for_order'] == '1'}

    @mapping
    def categ_id(self, record):
        return {'categ_id': self.get_openerp_id(
            'prestashop.product.category',
            record['id_category_default']
        )}

    @mapping
    def categ_ids(self, record):
        categories = record['associations']['categories']['category']
        if not isinstance(categories, list):
            categories = [categories]
        product_categories = []
        for category in categories:
            category_id = self.get_openerp_id(
                'prestashop.product.category',
                category['id']
            )
            product_categories.append(category_id)

        return {'categ_ids': [(6, 0, product_categories)]}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def ean13(self, record):
        #TODO who is the reference data prestashop ean13 or prestatshop ean13 ?
        if record['ean13'] == '0':
            return {}
        return {'ean13': record['ean13']}

    @mapping
    def taxes_id(self, record):
        if record['id_tax_rules_group'] == '0':
            return {}
        tax_group_id = self.get_openerp_id(
            'prestashop.account.tax.group',
            record['id_tax_rules_group']
        )
        tax_group_model = self.session.pool.get('account.tax.group')
        tax_ids = tax_group_model.read(
            self.session.cr,
            self.session.uid,
            tax_group_id,
            ['tax_ids']
        )
        return {"taxes_id": [(6, 0, tax_ids['tax_ids'])]}


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
        # TODO FIXME what name give to field present in
        # prestashop_product_product and product_product
        'always_available': fields.boolean(
            'Active',
            help='if check, this object is always available'),
        'sale_ok': fields.boolean(
            'For sale',
            help='see parent field'
        ),
        'quantity': fields.float(
            'Computed Quantity',
            help="Last computed quantity to send on Prestashop."
        ),
        'description_html': fields.html(
            'Description',
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
        'default_shop_id': fields.many2one(
            'prestashop.shop',
            'Default shop',
            required=True
        ),
        'link_rewrite': fields.char(
            'Friendly URL',
            translate=True,
            required=True,
        ),
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
            if new_qty != product.quantity:
                self.write(cr, uid, product.id,
                           {'quantity': new_qty},
                           context=context)
        return True

    def _prestashop_qty(self, cr, uid, product, context=None):
        if context is None:
            context = {}
        backend = product.backend_id
        stock = backend.warehouse_id.lot_stock_id
        #only for prestashop for now : stock_field is hardcoded
        #if backend.product_stock_field_id:
        #    stock_field = backend.product_stock_field_id.name
        #else:
        #    stock_field = 'virtual_available'
        stock_field = 'qty_available'
        location_ctx = context.copy()
        location_ctx['location'] = stock.id
        product_stk = self.read(cr, uid, product.id,
                                [stock_field],
                                context=location_ctx)
        return product_stk[stock_field]


@prestashop
class ProductAdapter(GenericAdapter):
    _model_name = 'prestashop.product.product'
    _prestashop_model = 'products'
    _export_node_name = 'product'

    def update_inventory(self, id, attributes):
        self._prestashop_model = 'stock_availables'
        self.write(id, attributes)


@prestashop
class ProductInventoryExport(ExportSynchronizer):
    _model_name = ['prestashop.product.product']

    def _get_data(self, product, fields):
        if 'quantity' in fields:
            return {
                'quantity': int(product.quantity),
                'id_product': product.prestashop_id,
                'id_product_attribute': 0,
                'depends_on_stock': 0,
                'out_of_stock': product.quantity > 0 and 1 or 0,
                'id': json.dumps({
                    "id_product": product.prestashop_id,
                    "id_product_attribute": 0
                }),
                'id_shop': product.default_shop_id.prestashop_id,
                #TODO FIXME: what datas
                #'id_shop_group': 0,
            }
        return {}

    def run(self, binding_id, fields):
        """ Export the product inventory to Prestashop """
        product = self.session.browse(self.model._name, binding_id)
        binder = self.get_binder_for_model()
        prestashop_id = binder.to_backend(product.id)
        attributes = {'stock_available': self._get_data(product, fields)}
        self.backend_adapter.update_inventory(prestashop_id, attributes)


# fields which should not trigger an export of the products
# but an export of their inventory
INVENTORY_FIELDS = ('quantity',
                    )


@on_record_write(model_names='prestashop.product.product')
def prestashop_product_stock_updated(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    inventory_fields = list(set(fields).intersection(INVENTORY_FIELDS))
    if inventory_fields:
        export_inventory.delay(session, model_name,
                               record_id, fields=inventory_fields,
                               priority=20)


@job
def export_inventory(session, model_name, record_id, fields=None):
    """ Export the inventory configuration and quantity of a product. """
    product = session.browse(model_name, record_id)
    backend_id = product.backend_id.id
    env = get_environment(session, model_name, backend_id)
    inventory_exporter = env.get_connector_unit(ProductInventoryExport)
    return inventory_exporter.run(record_id, fields)
