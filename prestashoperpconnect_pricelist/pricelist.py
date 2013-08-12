# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_pricelist for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#     All Rights Reserved
#     @author :
#     David BEAL <david.beal@akretion.com>
#     Sébastien BEAU <sebastien.beau@akretion.com>
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

from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.osv.osv import except_osv

from openerp.addons.connector.event import (
    on_record_create,
    on_record_write,
    on_record_unlink,
    )
from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    export_record,
    PrestashopExporter,
    )
from openerp.addons.prestashoperpconnect.unit.binder import PrestashopModelBinder
from openerp.addons.prestashoperpconnect.unit.mapper import PrestashopExportMapper
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter
#from openerp.addons.connector.exception import InvalidDataError
from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.prestashoperpconnect.consumer import _MODEL_NAMES, _BIND_MODEL_NAMES


_MODEL_NAMES.append('product.pricelist.item')

PRICELIST_FIELDS = [
        'product_id',
        'min_quantity',
        'base',
        'price_discount',
        'price_surcharge',
        'new_base_price',
        'let_base_price',
        'start_date',
        'end_date',
    ]

class pricelist_item_template(orm.Model):
    _inherit = "pricelist.item.template"

    #def _reduction_type(self, cr, uid, ids, field_names, arg, context=None):
    #    res={}
    #    for elm in self.browse(cr, uid, ids):
    #        result[elm.id] = {}
    #        result[elm.id]['newfield'] = val
    #    return result

    _columns = {
        'new_base_price': fields.float('New base price',
            digits_compute=dp.get_precision('Sale Price'),
            help="New base price : 'base price' field is not used in this case (specfic to PrestaShop)."
            ),
        'let_base_price': fields.boolean('Let base price',
            help="True if OpenERP like behavior with 'based on' field"
            ),
        #'reduction_type': fields.selection(
        #        (
        #            ('amount', _('Amount')),
        #            ('percentage', _('Percent.')),
        #        ),
        #    'Reduc. type',
        #    help="Prestashop type of reduction"
        #    ),
        'price_discount': fields.float('Price Discount', digits=(16,4)
            ),
    }

    _defaults = {
        'let_base_price': True,
    }

    def _check_price_elements(self, cr, uid, ids):
        for tpl in self.browse(cr, uid, ids):
            if tpl.price_discount:
                if tpl.price_discount > 0 or tpl.price_discount < -1:
                    raise except_osv(_('Error on discount for PrestaShop:'),
                        _("'Discount' must be between -1 and 0 for PrestaShop webservice.\n" \
                        "Discount of '%s' founded") \
                        % tpl.price_discount)
                    return False
        return True

    def onchange_price_presta(self, cr, uid, ids, discount, surcharge,
                                                                context=None):
        if discount != 0 and surcharge != 0:
            if context.get('reduction_type') == 'discount':
                value = {'price_surcharge': 0}
            else:
                value = {'price_discount': 0}
            return {'value': value}
        return True


    _constraints = [(
            _check_price_elements,
            'Error: Invalid',
            ['price_discount', 'price_surcharge']
        )]


class product_pricelist_item(orm.Model):
    _inherit = "product.pricelist.item"

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.pricelist.item',
            'openerp_id',
            string="PrestaShop Bindings"
            ),
        'new_base_price': fields.float(
            'New base price',
            digits_compute=dp.get_precision('Sale Price'),
            help="New base price : 'based on' field is not used in this case (specfic to PrestaShop)."
            ),
        'let_base_price': fields.boolean(
            'Let base price',
            help="True if OpenERP like behavior with 'based on' field"
            ),
        #'reduction_type': fields.selection(
        #        (
        #            ('', ''),
        #            ('amount', _('Amount')),
        #            ('percentage', _('Percent.')),
        #        ),
        #    'Reduc. type',
        #    help="Prestashop type of reduction"
        #    ),
    }

    _defaults = {
        'let_base_price': True,
        #'reduction_type': '',
    }

    def create(self, cr, uid, vals, context=None):
        res = super(product_pricelist_item, self).create(cr, uid, vals, context=context)
        presta_item_obj = self.pool['prestashop.product.pricelist.item']
        version_obj = self.pool['product.pricelist.version']
        shop_obj = self.pool['prestashop.shop']
        price_version_id = vals['price_version_id']
        pricelist_id = version_obj.browse(cr, uid, [price_version_id], context=context)[0].pricelist_id.id
        shop_ids = shop_obj.search(cr, uid, [('pricelist_id', '=',
                                              pricelist_id)], context=context)
        #TODO FIXME : mostly there is only one backend per shop : needs a clean solution for other situations
        if shop_ids:
            for shop in shop_obj.browse(cr, uid, shop_ids, context=context):
                backend_id = shop.prestashop_bind_ids[0].id
        backend_rec = []
        for shop_id in shop_ids:
            vals = {'backend_id': backend_id, 'shop_id': shop_id, 'openerp_id': res}
            backend_rec.append(presta_item_obj.create(cr, uid, vals, context=context))
        print 'res', res
        return res
    #
    #def write(self, cr, uid, ids, vals, context=None):
    #    print 'vals:', vals, 'ids', ids
    #    keys = vals.keys()
    #    if len(keys) > 1 or keysvals.get('price_version_id') is None:
    #        ps_item_obj = self.pool['prestashop.product.pricelist.item']
    #        print '    write en cours'
    #        res = super(product_pricelist_item, self).write(cr, uid, ids, vals, context=context)
    #        ps_item_ids = ps_item_obj.search(cr, uid,
    #                            [('openerp_id', 'in', ids)], context=context)
    #        ps_item_obj.write(cr, uid, ps_item_ids, {'update': True}, context=context)


class prestashop_product_pricelist_item(orm.Model):
    _name = 'prestashop.product.pricelist.item'
    _inherit = 'prestashop.binding'
    _inherits = {'product.pricelist.item': 'openerp_id'}


    def unlink(self, *args, **kwargs):
        import pdb;pdb.set_trace()
        return super(prestashop_product_pricelist_item, self).unlink(*args, **kwargs)


    _columns = {
        'openerp_id': fields.many2one(
            'product.pricelist.item',
            string='Pricelist item',
            required=True,
            ondelete='cascade'
        ),
        'shop_id': fields.many2one(
            'prestashop.shop',
            string='Shop'
        ),
    }


class PricelistBuilder(orm.Model):
    _inherit = "pricelist.builder"

    def _prepare_item_vals(self, cr, uid, tpl, builder_id, context=None):
        vals = super(PricelistBuilder, self)._prepare_item_vals(cr, uid, tpl, builder_id, context=context)
        name = vals['name']
        #if tpl.reduction_type:
        #    vals['reduction_type'] = tpl.reduction_type
        #    if tpl.reduction_type == 'amount':
        #        name += ', ' + _('(amount) ')
        vals['let_base_price'] = tpl.let_base_price
        if tpl.new_base_price:
            vals['new_base_price'] = tpl.new_base_price
            if tpl.let_base_price == False:
                name += ', '+_('base price') + ': ' + str(tpl.new_base_price)
        vals.update({'name': name})
        return vals


@on_record_create(model_names='prestashop.product.pricelist.item')
def prestashop_product_pricelist_item_created(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, fields)

@on_record_write(model_names='product.pricelist.item')
def product_pricelist_item_written(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields).intersection(set(PRICELIST_FIELDS)):
        model = session.pool.get(model_name)
        record = model.browse(session.cr, session.uid,
                       record_id, context=session.context)
        for binding in record.prestashop_bind_ids:
            print "  from item written:", model, '  bind', binding.id, '  f', fields
            export_record.delay(session, 'prestashop.product.pricelist.item',
                                                            binding.id, fields)


@prestashop
#class ProductPricelistItemAdapter(GenericAdapter):
class PricelistItemAdapter(GenericAdapter):
    _model_name = 'prestashop.product.pricelist.item'
    _prestashop_model = 'specific_prices'
    _export_node_name = 'specific_price'


@prestashop
#class PrestashopProductPricelistItemBinder(PrestashopModelBinder):
class PrestashopPricelistItemBinder(PrestashopModelBinder):
    _model_name = 'prestashop.product.pricelist.item'


@prestashop
class PricelistExport(PrestashopExporter):
    _model_name = 'prestashop.product.pricelist.item'


@prestashop
#class PrestashopProductPricelistItemExportMapper(PrestashopExportMapper):
class PrestashopPricelistItemExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.product.pricelist.item'

    direct = [
        # (erp_field, external_app_field),
        ('min_quantity', 'from_quantity'),
        ('product_id', 'id_product'),
        #('', ''),
    ]

    @mapping
    def dates(self, record):
        if record.start_date:
            start = record.start_date
        else:
            start =  '0000-00-00'
        if record.end_date:
            end = record.end_date
        else:
            end =  '0000-00-00'
        start += ' 00:00:00'
        end += ' 00:00:00'
        return { 'from': start, 'to': end, }

    @mapping
    def div(self, record):
        return {'id_cart': '0', 'id_country': '0'}

    @mapping
    def id_currency(self, record):
        return {'id_currency': '0'}

    @mapping
    def div2(self, record):
        #return {'id_customer': '0', 'id_group': '0', 'id_product': '11', 'id_shop': 1}
        return {'id_customer': '0', 'id_group': '0', 'id_shop': 1}

    @mapping
    def reduction(self, record):
        vals = {'reduction_type': 'percentage'}
        if record.price_surcharge != 0:
            vals.update({'reduction_type': 'amount'})
        if vals['reduction_type'] == 'amount':
            vals.update({'reduction': str(record.price_surcharge * (-1))})
        else:
            vals.update({'reduction': str(record.price_discount * (-1))})
        return vals

    @mapping
    def price(self, record):
        print '\n   record id, oe, nbp, lbp', record.id, record.openerp_id, record.new_base_price, record.let_base_price
        #import pdb;pdb.set_trace()
        if record.let_base_price == True:
            return {'price': -1.000000}
        else:
            return {'price': record.new_base_price}
