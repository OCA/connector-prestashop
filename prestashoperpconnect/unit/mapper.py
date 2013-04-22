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

import mimetypes

from openerp.tools.translate import _
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper)
from ..backend import prestashop

from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)


class PrestashopImportMapper(ImportMapper):

    def get_openerp_id(self, model, prestashop_id):
        '''
        Returns an openerp id from a model name and a prestashop_id.

        This permits to find the openerp id through the prestahop model in
        openerp.
        '''
        binder = self.get_binder_for_model(model)
        oerp_ps_id = binder.to_openerp(prestashop_id)

        model = self.session.pool.get(model)
        oerp_ps_object = model.read(
            self.session.cr,
            self.session.uid,
            oerp_ps_id
        )
        return oerp_ps_object['openerp_id'][0]


@prestashop
class ShopGroupImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.shop.group'

    direct = [('name', 'name')]

    @mapping
    def name(self, record):
        name = record['name']
        if name is None:
            name = _('Undefined')
        return {'name': name}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class ShopImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.shop'

    direct = [
        ('name', 'name'),
        ('id_shop_group', 'shop_group_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class PartnerCategoryImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.res.partner.category'

    direct = [
        ('name', 'name'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
    ]

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class PartnerImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.res.partner'

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('email', 'email'),
        ('newsletter', 'newsletter'),
        ('birthday', 'birthday'),
        ('company', 'company'),
        ('active',  'active'),
        ('note',  'comment'),
        ('id_shop_group', 'shop_group_id'),
        ('id_shop', 'shop_id'),
        ('id_default_group', 'default_category_id'),
    ]

    @mapping
    def name(self, record):
        name = ""
        if record['firstname']:
            name += record['firstname']
        if record['lastname']:
            if len(name) != 0:
                name += " "
            name += record['lastname']
        return {'name': name}

    @mapping
    def groups(self, record):
        groups = record['associations']['groups']['group']
        if not isinstance(groups, list):
            groups = [groups]
        partner_categories = []
        for group in groups:
            category_id = self.get_fk_id(
                'prestashop.res.partner.category',
                group['id']
            )
            partner_categories.append(category_id)

        return {'group_ids': [(6, 0, partner_categories)]}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def lang(self, record):
        oerp_lang_id = self.get_fk_id(
            'prestashop.res.lang',
            record['id_lang']
        )

        model = self.environment.session.pool.get('prestashop.res.lang')
        oerp_lang = model.read(
            self.session.cr,
            self.session.uid,
            oerp_lang_id,
        )
        return {'lang': oerp_lang['code']}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def is_company(self, record):
        # This is sad because we _have_ to have a company partner if we want to
        # store multiple adresses... but... well... we have customers who want
        # to be billed at home and be delivered at work... (...)...
        return {'is_company': True}


@prestashop
class AddressImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.address'

    direct = [
        ('address1', 'street'),
        ('address2', 'street2'),
        ('city', 'city'),
        ('other', 'comment'),
        ('phone', 'phone'),
        ('phone_mobile', 'mobile'),
        ('postcode', 'zip'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('vat_number', 'vat_number'),
        ('id_customer', 'prestashop_partner_id'),
    ]

    @mapping
    def parent_id(self, record):
        return {'parent_id': self.get_openerp_id(
            'prestashop.res.partner',
            record['id_customer']
        )}

    @mapping
    def name(self, record):
        name = ""
        if record['firstname']:
            name += record['firstname']
        if record['lastname']:
            if name:
                name += " "
            name += record['lastname']
        if record['alias']:
            if name:
                name += " "
            name += '('+record['alias']+')'
        return {'name': name}

    @mapping
    def customer(self, record):
        return {'customer': True}


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


@prestashop
class ProductMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product'

    direct = [
        ('name', 'name'),
        ('description', 'description'),
        ('weight', 'weight'),
        ('price', 'list_price'),
        ('active', 'active'),
        ('wholesale_price', 'standard_price'),
        ('price', 'lst_price'),
        ('reference', 'default_code'),
    ]

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


@prestashop
class ProductImageMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.image'

    direct = [
        ('content', 'file_db_store'),
    ]

    @mapping
    def product_id(self, record):
        return {'product_id': self.get_openerp_id(
            'prestashop.product',
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


@prestashop
class SaleOrderMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order'

    direct = [
        ('reference', 'name'),
    ]

    def _get_sale_order_lines(self, record):
        return record['associations']['order_rows']['order_row']

    children = [
        (
            _get_sale_order_lines,
            'prestashop_order_line_ids',
            'prestashop.sale.order.line'
        ),
    ]

    def _map_child(self, record, from_attr, to_attr, model_name):
        # TODO patch ImportMapper in connector to support callable
        if callable(from_attr):
            child_records = from_attr(self, record)
        else:
            child_records = record[from_attr]
        
        self._data_children[to_attr] = []
        for child_record in child_records:
            mapper = self._init_child_mapper(model_name)
            mapper.convert_child(child_record, parent_values=record)
            self._data_children[to_attr].append(mapper)

    @mapping
    def shop_id(self, record):
        return {'shop_id': self.get_openerp_id(
            'prestashop.shop',
            record['id_shop']
        )}

    @mapping
    def partner_id(self, record):
        return {'partner_id': self.get_openerp_id(
            'prestashop.res.partner',
            record['id_customer']
        )}

    @mapping
    def partner_invoice_id(self, record):
        return {'partner_invoice_id': self.get_openerp_id(
            'prestashop.address',
            record['id_address_invoice']
        )}

    @mapping
    def partner_shipping_id(self, record):
        return {'partner_shipping_id': self.get_openerp_id(
            'prestashop.address',
            record['id_address_delivery']
        )}

    @mapping
    def pricelist_id(self, record):
        return {'pricelist_id': 1}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def payment(self, record):
        if record['payment']:
            model = self.session.pool.get('payment.method')
            payment_method_id = model.get_or_create_payment_method(
                self.session.cr,
                self.session.uid,
                record['payment'],
                self.session.context
            )
            return {'payment_method_id': payment_method_id}
        return {}

    def _after_mapping(self, result):
        sess = self.session
        result = sess.pool['sale.order']._convert_special_fields(
            sess.cr,
            sess.uid,
            result,
            result['prestashop_order_line_ids'],
            sess.context
        )
        onchange = self.get_connector_unit_for_model(SaleOrderOnChange)
        return onchange.play(result, result['prestashop_order_line_ids'])


@prestashop
class SaleOrderLineMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.line'
    
    direct = [
        ('product_name', 'name'),
        ('id', 'sequence'),
        ('product_price', 'price_unit'),
        ('product_quantity', 'product_uom_qty'),
    ]

    @mapping
    def product_id(self, record):
        return {'product_id': self.get_openerp_id(
            'prestashop.product',
            record['product_id']
        )}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class TaxGroupMapper(PrestashopImportMapper):
    _model_name = 'prestashop.account.tax.group'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
