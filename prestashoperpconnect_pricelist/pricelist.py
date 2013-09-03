# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_pricelist for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#     All Rights Reserved
#     @author :
#     David BEAL <david.beal@akretion.com>
#     Sébastien BEAU <sebastien.beau@akretion.com>
#     Guewen Baconnier (camptocamp)
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
from openerp.addons.prestashoperpconnect.unit.delete_synchronizer import PrestashopDeleteSynchronizer
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter
from openerp.addons.connector.unit.mapper import mapping

import openerp.addons.prestashoperpconnect.consumer as prestashoperpconnect

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


class PricelistItemTemplate(orm.Model):
    _inherit = "pricelist.item.template"

    def _check_min_quantity(self, cr, uid, ids):
        for item in self.browse(cr, uid, ids):
            if item.min_quantity < 1:
                raise except_osv(_('Error in quantity:'),
                    _("'Minimum quantity' must be greater than 1. " \
                    "Quantity '%s' founded") \
                    % item.min_quantity)
                return False
        return True

    _constraints = [(_check_min_quantity,
        'Error: Invalid quantity',
        ['min_quantity'])]


class pricelist_item_template(orm.Model):
    """ - add specific fields for prestashop api
        - check validity of these fields
    """
    _inherit = "pricelist.item.template"

    _columns = {
        'new_base_price': fields.float('New price',
            digits_compute=dp.get_precision('Sale Price'),
            help="New base price : 'base price' field is not used in this case (specific to PrestaShop)."
            ),
        'let_base_price': fields.boolean('Let price',
            help="If False, use the 'New price' field (specific to Prestashop) instead of 'based on' field"
            ),
        'price_discount': fields.float('Price Discount', digits=(16,4)
            ),
    }

    _defaults = {
        'let_base_price': True,
    }

    def _check_price_elements(self, cr, uid, ids):
        "check quantity"
        for item_tpl in self.browse(cr, uid, ids):
            if item_tpl.price_discount:
                if item_tpl.price_discount > 0 or item_tpl.price_discount < -1:
                    raise except_osv(_('Error on discount for PrestaShop:'),
                        _("'Discount' must be between -1 and 0 for PrestaShop webservice.\n" \
                        "Discount of '%s' founded") \
                        % item_tpl.price_discount)
                    return False
        return True

    def onchange_price_presta(self, cr, uid, ids, discount, surcharge,
                                                                context=None):
        """Prestashop do not support in the same time 'price_discount'
            and 'price_surcharge' fields : either one or the other
            On change mechanism allow to switch from one to the other """
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
            # TODO check needs conditon on price_surcharge ?
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
            help="If true the behavior is like in OpenERP alone (with 'based on' field)"
            ),
    }

    _defaults = {
        'let_base_price': True,
    }

    def create(self, cr, uid, vals, context=None):
        res = super(product_pricelist_item, self).create(cr, uid, vals, context=context)
        presta_item_m = self.pool['prestashop.product.pricelist.item']
        version_m = self.pool['product.pricelist.version']
        shop_m = self.pool['prestashop.shop']
        price_version_id = vals['price_version_id']
        pricelist = version_m.browse(cr, uid, [price_version_id], context=context)[0].pricelist_id
        ## search shops using current pricelist
        shop_ids = shop_m.search(cr, uid, [('pricelist_id', '=',
                                              pricelist.id)], context=context)
        #TODO FIXME : mostly there is only one backend per shop : needs a clean solution for other situations
        if shop_ids:
            for shop in shop_m.browse(cr, uid, shop_ids, context=context):
                backend_id = shop.prestashop_bind_ids[0].id
                vals = {'backend_id': backend_id,
                        'shop_id': shop.id,
                        'openerp_id': res}
                ## creation of 'prestas..product.pricel..item' record by shop
                presta_item_m.create(cr, uid, vals, context=context)
        else:
            raise except_osv("Error with PrestaShop: ",
                unicode("""There is no shop connected with PrestaShop with this pricelist :
                    '%s'\nNo synchronisation """ % pricelist.name) + \
                unicode ("of this pricelist is possible with PrestaShop"))
            #self.pool.get('mail.thread').message_post(cr, uid, False, "mess mine", context=context, partner_ids=[(6, 0, [1])], subtype='__.notify')
        return res


class prestashop_product_pricelist_item(orm.Model):
    _name = 'prestashop.product.pricelist.item'
    _inherit = 'prestashop.binding'
    _inherits = {'product.pricelist.item': 'openerp_id'}

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

    _columns = {
        'partner_cat_id': fields.many2one(
            'res.partner.category',
            'Partner Categ.',
            domain=[('prestashop_bind_ids', '!=', False)],
            help="NOT USED by OpenERP to modify pricelist computation (only " \
                "with external connected applications)"
        ),
    }

    def _prepare_item_vals(self, cr, uid, item_tpl, builder_o, context=None):
        vals = super(PricelistBuilder, self)._prepare_item_vals(cr, uid, item_tpl,
                                                    builder_o, context=context)
        vals['let_base_price'] = item_tpl.let_base_price
        if item_tpl.new_base_price:
            vals['new_base_price'] = item_tpl.new_base_price
        return vals

    def product_filter(self, cr, uid, product_ids, context=None):
        product_m = self.pool['product.product']
        for product in product_m.browse(cr, uid, product_ids, context=context):
            if not product.prestashop_bind_ids:
                product_ids.remove(product.id)
        return product_ids

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
            export_record.delay(session, 'prestashop.product.pricelist.item',
                                                            binding.id, fields)

@on_record_unlink(model_names='product.pricelist.item')
def delay_unlink_all_bindings(session, model_name, record_id):
    prestashoperpconnect.delay_unlink_all_bindings(session, model_name, record_id)


@prestashop
class PricelistItemAdapter(GenericAdapter):
    _model_name = 'prestashop.product.pricelist.item'
    _prestashop_model = 'specific_prices'
    _export_node_name = 'specific_price'


@prestashop
class PrestashopPricelistItemBinder(PrestashopModelBinder):
    _model_name = 'prestashop.product.pricelist.item'


@prestashop
class PricelistExport(PrestashopExporter):
    _model_name = 'prestashop.product.pricelist.item'


@prestashop
class PrestashopPricelistItemExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.product.pricelist.item'

    direct = [
        # (erp_field, external_app_field),
        ('min_quantity', 'from_quantity'),
        ('product_id', 'id_product'),
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
    def id_country(self, record):
        binder = self.get_binder_for_model('prestashop.res.country')
        id_country = binder.to_backend(record.country_id.id, unwrap=True)
        if not id_country:
            id_country = 0
        return {'id_country': id_country}

    @mapping
    def id_shop(self, record):
        return {'id_shop': record.shop_id.id}

    @mapping
    def id_currency(self, record):
        binder = self.get_binder_for_model('prestashop.res.currency')
        currency_id = binder.to_backend(
            record.price_version_id.pricelist_id.currency_id.id, unwrap=True)
        return {'id_currency': currency_id}

    @mapping
    def id_group(self, record):
        binder = self.get_binder_for_model('prestashop.res.partner.category')
        id_group = binder.to_backend(record.partner_cat_id.id, unwrap=True)
        if not id_group:
            id_group = 0
        return {'id_group': id_group}

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
        if record.let_base_price == True:
            return {'price': -1.000000}
        else:
            return {'price': record.new_base_price}

    @mapping
    def unused_in_erp_but_mandatory_in_presta(self, record):
        return {'id_customer': '0', 'id_cart': '0'}

@prestashop
class PrestashopPricelistItemDeleteSynchronizer(PrestashopDeleteSynchronizer):
    _model_name = 'prestashop.product.pricelist.item'