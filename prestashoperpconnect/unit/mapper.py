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

from openerp.tools.translate import _
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper,
    ExportMapper
)
from ..backend import prestashop
from backend_adapter import GenericAdapter
from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)


class PrestashopImportMapper(ImportMapper):

    def get_openerp_id(self, model, prestashop_id):
        '''
        Returns an openerp id from a model name and a prestashop_id.

        This permits to find the openerp id through the external application
        model in Erp.
        '''
        binder = self.get_binder_for_model(model)
        erp_ps_id = binder.to_openerp(prestashop_id)

        model = self.session.pool.get(model)
        erp_ps_object = model.read(
            self.session.cr,
            self.session.uid,
            erp_ps_id,
            ['openerp_id'],
            context=self.session.context
        )
        return erp_ps_object['openerp_id'][0]


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
        ('company', 'company'),
        ('active', 'active'),
        ('note', 'comment'),
        ('id_shop_group', 'shop_group_id'),
        ('id_shop', 'shop_id'),
        ('id_default_group', 'default_category_id'),
    ]

    @mapping
    def birthday(self, record):
        if record['birthday'] in ['0000-00-00', '']:
            return {}
        return {'birthday': record['birthday']}

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
            binder = self.get_binder_for_model(
                'prestashop.res.partner.category'
            )
            category_id = binder.to_openerp(group['id'])
            partner_categories.append(category_id)

        return {'group_ids': [(6, 0, partner_categories)]}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def lang(self, record):
        binder = self.get_binder_for_model('prestashop.res.lang')
        erp_lang_id = binder.to_openerp(record['id_lang'])
        #hack
        record['id_lang'] = 1
        model = self.environment.session.pool.get('prestashop.res.lang')
        erp_lang = model.read(
            self.session.cr,
            self.session.uid,
            erp_lang_id,
        )
        return {'lang': erp_lang['code']}

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
class SaleOrderStateMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.state'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class SaleOrderMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order'

    direct = [
        ('reference', 'name'),
        ('date_add', 'date_order'),
        ('invoice_number','prestashop_invoice_number'),
        ('delivery_number','prestashop_delivery_number'),
        ('total_paid', 'total_paid'),
    ]

    def _get_sale_order_lines(self, record):
        orders = record['associations']['order_rows']['order_row']
        if isinstance(orders, dict):
            return [orders]
        return orders

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
            adapter = self.get_connector_unit_for_model(GenericAdapter,
                                                        model_name)
            detail_record = adapter.read(child_record['id'])

            mapper = self._init_child_mapper(model_name)
            mapper.convert_child(detail_record, parent_values=record)
            self._data_children[to_attr].append(mapper)

    @mapping
    def shipping(self, record):
        shipping_tax_incl = float(record['total_shipping_tax_incl'])
        shipping_tax_excl = float(record['total_shipping_tax_excl'])
        return {
            'shipping_amount_tax_included': shipping_tax_incl,
            'shipping_amount_tax_excluded': shipping_tax_excl,
        }

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
        method_ids = self.session.search('payment.method',
                                         [['name', '=', record['payment']]])
        assert method_ids, ("Payment method '%s' has not been found ; "
                            "you should create it manually (in Sales->"
                            "Configuration->Sales->Payment Methods" %
                            record['payment'])
        method_id = method_ids[0]
        return {'payment_method_id': method_id}

    @mapping
    def carrier_id(self, record):
        return {'carrier_id': self.get_openerp_id(
            'prestashop.delivery.carrier',
            record['id_carrier']
        )}

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
        ('reduction_percent', 'discount'),
    ]

    @mapping
    def product_id(self, record):
        return {'product_id': self.get_openerp_id(
            'prestashop.product.product',
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


class PrestashopExportMapper(ExportMapper):

    def _map_direct(self, record, from_attr, to_attr):
        res = super(PrestashopExportMapper, self)._map_direct(record,
                                                              from_attr,
                                                              to_attr)
        column = self.model._all_columns[from_attr].column
        if column._type == 'boolean':
            return res and 1 or 0
        return res


class TranslationPrestashopExportMapper(PrestashopExportMapper):

    def convert(self, records_by_language, fields=None):
        self.records_by_language = records_by_language
        first_key = records_by_language.keys()[0]
        self._convert(records_by_language[first_key], fields=fields)
        self._data.update(self.convert_languages(self.translatable_fields))

    def convert_languages(self, translatable_fields):
        res = {}
        for from_attr, to_attr in translatable_fields:
            value = {'language': []}
            for language_id, record in self.records_by_language.items():
                value['language'].append({
                    'attrs': {'id': str(language_id)},
                    'value': record[from_attr]
                })
            res[to_attr] = value
        return res
