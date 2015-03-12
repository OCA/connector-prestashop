'''
A product combination is a product with different attributes in prestashop.
In prestashop, we can sell a product or a combination of a product with some
attributes.

For example, for the iPod product we can found in demo data, it has some
combinations with different colors and different storage size.

We map that in OpenERP to a product.product with an attribute.set defined for
the main product.
'''

from openerp.osv import fields, orm

from openerp.addons.connector.session import ConnectorSession

from ..unit.import_synchronizer import import_record


class product_product(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'prestashop_combinations_bind_ids': fields.one2many(
            'prestashop.product.combination',
            'openerp_id',
            string='PrestaShop Bindings (combinations)'
        ),
    }


class prestashop_product_combination(orm.Model):
    _name = 'prestashop.product.combination'
    _inherit = 'prestashop.binding'
    _inherits = {'product.product': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.product',
            string='Product',
            required=True,
            ondelete='cascade'
        ),
        'main_template_id': fields.many2one(
            'prestashop.product.template',
            string='Main Template',
            required=True,
            ondelete='cascade'
        ),
        'quantity': fields.float(
            'Computed Quantity',
            help="Last computed quantity to send on Prestashop."
        ),
        'reference': fields.char('Original reference'),
        'default_on': fields.boolean('Available For Order'),
    }

    def recompute_prestashop_qty(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]

        for product in self.browse(cr, uid, ids, context=context):
            new_qty = self._prestashop_qty(cr, uid, product, context=context)
            self.write(
                cr, uid, product.id, {'quantity': new_qty}, context=context
            )
        return True

    def _prestashop_qty(self, cr, uid, product, context=None):
        return product.qty_available


class product_attribute(orm.Model):
    _inherit = 'product.attribute'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.combination.option',
            'openerp_id',
            string='PrestaShop Bindings (combinations)'
        ),
    }


class prestashop_product_combination_option(orm.Model):
    _name = 'prestashop.product.combination.option'
    _inherit = 'prestashop.binding'
    _inherits = {'product.attribute': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.attribute',
            string='Attribute',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_position': fields.integer('Prestashop Position'),
        'group_type': fields.selection([('color','Color'),
                                        ('radio', 'Radio'),
                                        ('select', 'Select')],'Type'),
        'public_name': fields.char(
            'Public Name',
            translate=True
        ),

    }
    
    _defaults = {
                 'group_type': 'select',
                 }


class product_attribute_value(orm.Model):
    _inherit = 'product.attribute.value'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.combination.option.value',
            'openerp_id',
            string='PrestaShop Bindings'
        ),
    }


class prestashop_product_combination_option_value(orm.Model):
    _name = 'prestashop.product.combination.option.value'
    _inherit = 'prestashop.binding'
    _inherits = {'product.attribute.value': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.attribute.value',
            string='Attribute',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_position': fields.integer('Prestashop Position'),
        'id_attribute_group': fields.many2one('prestashop.product.combination.option')
    }

    _defaults = {
        'prestashop_position': 1
    }
