# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright (C) 2015 Tech-Receptives(<http://www.tech-receptives.com>)
#    Copyright 2013 Camptocamp SA
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    @author: Guewen Baconnier
#    @author Parthiv Patel <parthiv@techreceptives.com>
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


from decimal import Decimal
from backend_adapter import GenericAdapter
from backend_adapter import PrestaShopCRUDAdapter
from openerp.addons.connector.connector import Binder
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper,
    ExportMapper
)
from openerp.addons.connector.unit.mapper import only_create
from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)
from openerp.tools.translate import _
from ..backend import prestashop
from ..connector import add_checkpoint


class PrestashopImportMapper(ImportMapper):

    # get_openerp_id is deprecated use the binder intead
    # we should have only 1 way to map the field to avoid error

    #     @api.one

    def get_openerp_id(self, model, prestashop_id):
        '''
        Returns an openerp id from a model name and a prestashop_id.

        This permits to find the openerp id through the external application
        model in Erp.
        '''
        binder = self.get_binder_for_model(model)
        erp_ps_id = binder.to_openerp(prestashop_id)
        if erp_ps_id is None:
            return None

        model = self.session.pool.get(model)
        return erp_ps_id.openerp_id.id


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

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def warehouse_id(self, record):
        return {'warehouse_id': self.backend_record.warehouse_id.id}

    @mapping
    def opener_id(self, record):
        return {'openerp_id': self.backend_record.warehouse_id.id}

    @mapping
    def shop_group_id(self, record):
        shop_group_binder = self.get_binder_for_model('prestashop.shop.group')
        shop_group_id = shop_group_binder.to_openerp(
            record['id_shop_group'])
        if not shop_group_id:
            return {}
        return {'shop_group_id': shop_group_id.id}


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

    @mapping
    def name(self, record):
        name = None
        if 'language' in record['name']:
            language_binder = self.get_binder_for_model('prestashop.res.lang')
            languages = record['name']['language']
            if not isinstance(languages, list):
                languages = [languages]
            for lang in languages:
                erp_language_id = language_binder.to_openerp(
                    lang['attrs']['id'])
                if not erp_language_id:
                    continue
                erp_lang = self.session.read(
                    'prestashop.res.lang',
                    erp_language_id.id,
                    []
                )
                if erp_lang['code'] == 'en_US':
                    name = lang['value']
                    break
            if name is None:
                name = languages[0]['value']
        else:
            name = record['name']

        return {'name': name}


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
    def pricelist(self, record):
        binder = self.get_connector_unit_for_model(
            Binder, 'prestashop.groups.pricelist')
        pricelist_id = binder.to_openerp(
            record['id_default_group'], unwrap=True)
        if not pricelist_id:
            return {}
        return {'property_product_pricelist': pricelist_id.id}

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
        groups = record.get('associations', {}).get(
            'groups', {}).get('group', [])
        if not isinstance(groups, list):
            groups = [groups]
        partner_categories = []
        for group in groups:
            binder = self.get_binder_for_model(
                'prestashop.res.partner.category'
            )
            category_id = binder.to_openerp(group['id'])
            partner_categories.append(category_id.id)

        return {'category_id': [(6, 0, partner_categories)]}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def lang(self, record):
        binder = self.get_binder_for_model('prestashop.res.lang')
        erp_lang_id = None
        if record.get('id_lang'):
            erp_lang_id = binder.to_openerp(record['id_lang'])
        if erp_lang_id is None:
            data_obj = self.session.pool.get('ir.model.data')
            erp_lang_id = data_obj.get_object_reference(
                self.session.cr,
                self.session.uid,
                'base',
                'lang_en')[1]
        model = self.environment.session.pool.get('prestashop.res.lang')

        erp_lang = model.read(
            self.session.cr,
            self.session.uid,
            erp_lang_id.id,
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

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def shop_id(self, record):
        shop_binder = self.get_binder_for_model('prestashop.shop')
        shop_id = shop_binder.to_openerp(
            record['id_shop'])
        if not shop_id:
            return {}
        return {'shop_id': shop_id.id}

    @mapping
    def shop_group_id(self, record):
        shop_group_binder = self.get_binder_for_model('prestashop.shop.group')
        shop_group_id = shop_group_binder.to_openerp(
            record['id_shop_group'])
        if not shop_group_id:
            return {}
        return {'shop_group_id': shop_group_id.id}

    @mapping
    def default_category_id(self, record):
        category_binder = self.get_binder_for_model(
            'prestashop.res.partner.category')
        default_category_id = category_binder.to_openerp(
            record['id_default_group'])
        if not default_category_id:
            return {}
        return {'default_category_id': default_category_id.id}


@prestashop
class SupplierMapper(PrestashopImportMapper):
    _model_name = 'prestashop.supplier'

    direct = [
        ('name', 'name'),
        ('id', 'prestashop_id'),
        ('active', 'active'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def supplier(self, record):
        return {
            'supplier': True,
            'is_company': True,
            'customer': False,
        }

    @mapping
    def image(self, record):
        supplier_image_adapter = self.get_connector_unit_for_model(
            PrestaShopCRUDAdapter, 'prestashop.supplier.image'
        )
        try:
            return {'image': supplier_image_adapter.read(record['id'])}
        except:
            return {}


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
        ('id_customer', 'prestashop_partner_id'),
    ]

    @mapping
    def parent_id(self, record):
        parent_id = self.get_openerp_id(
            'prestashop.res.partner',
            record['id_customer']
        )
        if record['vat_number']:
            vat_number = record['vat_number'].replace('.', '').replace(' ', '')
            if self._check_vat(vat_number):
                self.session.write(
                    'res.partner',
                    [parent_id],
                    {'vat': vat_number}
                )
            else:
                add_checkpoint(
                    self.session,
                    'res.partner',
                    parent_id,
                    self.backend_record.id
                )
        return {'parent_id': parent_id}

    def _check_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:]
        return self.session.pool['res.partner'].simple_vat_check(
            self.session.cr,
            self.session.uid,
            vat_country,
            vat_number,
            context=self.session.context
        )

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
            name += '(' + record['alias'] + ')'
        return {'name': name}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def country(self, record):
        if record.get('id_country'):
            binder = self.get_binder_for_model('prestashop.res.country')
            erp_country_id = binder.to_openerp(
                record['id_country'], unwrap=True)
            return {'country_id': erp_country_id.id}
        return {}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def prestashop_partner_id(self, record):
        partner_binder = self.get_binder_for_model('prestashop.res.partner')
        if record['id_customer']:
            prestashop_partner_id = partner_binder.to_openerp(
                record['id_customer'])
        if not prestashop_partner_id:
            return {}
        return {'prestashop_partner_id': prestashop_partner_id.id}


@prestashop
class SaleOrderStateMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.state'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


@prestashop
class SaleOrderMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order'

    direct = [
        ('date_add', 'date_order'),
        ('invoice_number', 'prestashop_invoice_number'),
        ('delivery_number', 'prestashop_delivery_number'),
        ('total_paid', 'total_amount'),
        ('total_shipping_tax_incl', 'total_shipping_tax_included'),
        ('total_shipping_tax_excl', 'total_shipping_tax_excluded')
    ]

    def _get_sale_order_lines(self, record):
        orders = record['associations'].get(
            'order_rows', {}).get('order_row', [])
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

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        # TODO patch ImportMapper in connector to support callable
        if callable(from_attr):
            child_records = from_attr(self, source)
        else:
            child_records = source[from_attr]

        children = []
        for child_record in child_records:
            adapter = self.get_connector_unit_for_model(GenericAdapter,
                                                        model_name)
            detail_record = adapter.read(child_record['id'])

            mapper = self._get_map_child_unit(model_name)
            items = mapper.get_items(
                [detail_record], map_record, to_attr, options=self.options
            )
            children.extend(items)

        discount_lines = self._get_discounts_lines(source)
        children.extend(discount_lines)
        return children

    def _get_discounts_lines(self, record):
        if record['total_discounts'] == '0.00':
            return []
        adapter = self.get_connector_unit_for_model(
            GenericAdapter, 'prestashop.sale.order.line.discount')
        discount_ids = adapter.search({'filter[id_order]': record['id']})
        discount_mappers = []
        for discount_id in discount_ids:
            discount = adapter.read(discount_id)
            mapper = self._init_child_mapper(
                'prestashop.sale.order.line.discount')
            # map_record = mapper.map_record(discount, parent=record)
            # map_values = map_record.values()
            # discount_mappers.append(map_values)
            mapper.convert_child(discount, parent_values=record)
            discount_mappers.append(mapper)
        return discount_mappers

    def _sale_order_exists(self, name):
        ids = self.session.search('sale.order', [
            ('name', '=', name),
            ('company_id', '=', self.backend_record.company_id.id),
        ])
        return len(ids) == 1

    @mapping
    def name(self, record):
        basename = record['reference']
        if not self._sale_order_exists(basename):
            return {"name": basename}
        i = 1
        name = basename + '_%d' % (i)
        while self._sale_order_exists(name):
            i += 1
            name = basename + '_%d' % (i)
        return {"name": name}

    @mapping
    def shipping(self, record):
        shipping_tax_incl = float(record['total_shipping_tax_incl'])
#         shipping_tax_excl = float(record['total_shipping_tax_excl'])
        return {
            'shipping_amount_tax_included': shipping_tax_incl,
            'shipping_amount_tax_excluded': shipping_tax_incl,
        }

    @mapping
    def shop_id(self, record):
        if record['id_shop'] == '0':
            shop_ids = self.session.search('prestashop.shop', [
                ('backend_id', '=', self.backend_record.id)
            ])
            shop = self.session.read(
                'prestashop.shop', shop_ids[0], ['openerp_id'])
            return {'shop_id': shop['openerp_id'][0]}
        shop_id = self.get_openerp_id(
            'prestashop.shop',
            record['id_shop']
        )
        return {'shop_id': shop_id}

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
        pricelist_id = self.session.search(
            'product.pricelist',
            [('currency_id', '=',
                self.backend_record.company_id.currency_id.id),
                ('type', '=', 'sale')])
        if pricelist_id:
            return {'pricelist_id': pricelist_id[0]}
        return {}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def payment(self, record):
        method_ids = self.session.search(
            'payment.method',
            [
                ('name', '=', record['payment']),
                ('company_id', '=', self.backend_record.company_id.id),
            ]
        )
        assert method_ids, ("Payment method '%s' has not been found ; "
                            "you should create it manually (in Sales->"
                            "Configuration->Sales->Payment Methods" %
                            record['payment'])
        method_id = method_ids[0]
        return {'payment_method_id': method_id}

    @mapping
    def carrier_id(self, record):
        if record['id_carrier'] == '0':
            return {}
        return {'carrier_id': self.get_openerp_id(
            'prestashop.delivery.carrier',
            record['id_carrier']
        )}

    @mapping
    def amount_tax(self, record):
        tax = float(record['total_paid_tax_incl'])\
            - float(record['total_paid_tax_excl'])
        return {'amount_tax': tax}

    def _after_mapping(self, result):
        sess = self.session
        backend = self.backend_record
        order_line_ids = []
        if 'prestashop_order_line_ids' in result:
            order_line_ids = result['prestashop_order_line_ids']
        taxes_included = backend.taxes_included
        with self.session.change_context({'is_tax_included': taxes_included}):
            result = sess.pool['sale.order']._convert_special_fields(
                sess.cr,
                sess.uid,
                result,
                order_line_ids,
                sess.context
            )
        onchange = self.get_connector_unit_for_model(SaleOrderOnChange)
        order_line_ids = []
        if 'prestashop_order_line_ids' in result:
            order_line_ids = result['prestashop_order_line_ids']
        return onchange.play(result, order_line_ids)


@prestashop
class SaleOrderLineMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.line'

    direct = [
        ('product_name', 'name'),
        ('id', 'sequence'),
        ('product_quantity', 'product_uom_qty'),
        ('reduction_percent', 'discount'),
    ]

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}

    def none_product(self, record):
        product_id = True
        if 'product_attribute_id' not in record:

            template_id = self.get_openerp_id(
                'prestashop.product.template',
                record['product_id'])

            product_id = self.session.search('product.product', [
                ('product_tmpl_id', '=', template_id),
                ('company_id', '=', self.backend_record.company_id.id)])
        return not product_id

    @mapping
    def price_unit(self, record):
        if self.backend_record.taxes_included:
            key = 'unit_price_tax_incl'
        else:
            key = 'unit_price_tax_excl'
        if record['reduction_percent']:
            reduction = Decimal(record['reduction_percent'])
            price = Decimal(record[key])
            price_unit = price / ((100 - reduction) / 100)
        else:
            price_unit = record[key]
        return {'price_unit': price_unit}

    @mapping
    def product_id(self, record):
        if 'product_attribute_id' in record and \
                record.get('product_attribute_id') != '0':
            combination_binder = self.get_binder_for_model(
                'prestashop.product.combination')
            product_id = combination_binder.to_openerp(
                record['product_attribute_id'],
                unwrap=True
            )
            if product_id:
                product_id = product_id.id
        else:
            template_id = self.get_openerp_id(
                'prestashop.product.template',
                record['product_id'])
            product_id = self.session.search('product.product', [
                ('product_tmpl_id', '=', template_id),
                ('company_id', '=', self.backend_record.company_id.id)])
            if product_id:
                product_id = product_id[0]
            if product_id is None:
                return self.tax_id(record)
        return {'product_id': product_id}

    def _find_tax(self, ps_tax_id):
        binder = self.get_binder_for_model('prestashop.account.tax')
        openerp_id = binder.to_openerp(ps_tax_id, unwrap=True)
        tax = self.session.read(
            'account.tax', openerp_id.id,
            ['price_include', 'related_inc_tax_id'])

        if self.backend_record.taxes_included and not \
                tax['price_include'] and tax['related_inc_tax_id']:
            return tax['related_inc_tax_id'][0]

        return openerp_id

    @mapping
    def tax_id(self, record):
        if self.backend_record.taxes_included:
            taxes = record.get('associations', {}).get(
                'taxes', {}).get('tax', [])
            if not isinstance(taxes, list):
                taxes = [taxes]
            result = []
            for tax in taxes:
                openerp_id = self._find_tax(tax['id'])
                if openerp_id:
                    result.append(openerp_id.id)
            if result:
                return {'tax_id': [(6, 0, result)]}
        return {}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class SaleOrderLineDiscount(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.line.discount'

    direct = []

    @mapping
    def discount(self, record):
        return {
            'name': _('Discount %s') % (record['name']),
            'product_uom_qty': 1,
        }

    @mapping
    def price_unit(self, record):
        price_unit = record['value_tax_excl']
        if price_unit[0] != '-':
            price_unit = '-' + price_unit
        return {'price_unit': price_unit}

    @mapping
    def product_id(self, record):
        if self.backend_record.discount_product_id:
            return {'product_id': self.backend_record.discount_product_id.id}
        data_obj = self.session.pool.get('ir.model.data')
        model_name, product_id = data_obj.get_object_reference(
            self.session.cr,
            self.session.uid,
            'connector_ecommerce',
            'product_product_discount'
        )
        return {'product_id': product_id}

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

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


@prestashop
class TaxMapper(PrestashopImportMapper):
    _model_name = 'prestashop.account.tax'

    direct = [
        ('name', 'name'),
        ('rate', 'amount'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def price_include(self, record):
        return {'price_include': self.backend_record.taxes_included}

    @mapping
    def amount(self, record):
        return {'amount': float(record['rate']) / 100}

    @mapping
    def name(self, record):
        name = None
        if 'language' in record['name']:
            language_binder = self.get_binder_for_model('prestashop.res.lang')
            languages = record['name']['language']
            if not isinstance(languages, list):
                languages = [languages]
            for lang in languages:
                erp_language_id = language_binder.to_openerp(
                    lang['attrs']['id'])
                if not erp_language_id:
                    continue
                erp_lang = self.session.read(
                    'prestashop.res.lang',
                    erp_language_id.id,
                    []
                )
                if erp_lang['code'] == 'en_US':
                    name = lang['value']
                    break
            if name is None:
                name = languages[0]['value']
        else:
            name = record['name']

        return {'name': name}


@prestashop
class ConfigurationMapper(PrestashopImportMapper):
    _model_name = 'prestashop.configuration'

    direct = [
        ('name', 'name'),
        ('value', 'value'),
    ]

    @mapping
    def backend_id(self, record):
        currency_ids = self.session.search('prestashop.res.currency', [])
        currency_binder = self.get_binder_for_model(
            'prestashop.res.currency')
        for c_id in currency_ids:
            currency_id = currency_binder.to_openerp(
                c_id,
                unwrap=True
            )
            pricelist_id = self.session.search(
                'product.pricelist', [('currency_id', '=', currency_id.id),
                                      ('type', '=', 'sale')])
            if not pricelist_id:
                item = {
                    'min_quantity': 0,
                    'sequence': 5,
                    'base': 1,
                    'price_discount': 0  # -float(record['reduction']) / 100.0,
                }
                version = {
                    'name': 'Version',
                    'active': True,
                    'items_id': [(0, 0, item)],
                }
                self.session.create('product.pricelist', {
                                    'name': 'Sale Pricelist',
                                    'active': True, 'type': 'sale',
                                    'currency_id': currency_id.id,
                                    'version_id': [(0, 0, version)]})

        if record['name'] == 'PS_TAX':
            if record['value'] == '1':
                included = True
            else:
                included = False

            self.session.write(
                'prestashop.backend',
                [self.backend_record.id],
                {'taxes_included': included}
            )
        if record['name'] == 'PS_CURRENCY_DEFAULT':
            currency_binder = self.get_binder_for_model(
                'prestashop.res.currency')
            currency_id = currency_binder.to_openerp(
                int(record['value']),
                unwrap=True
            )
            self.session.write('res.company',
                               [self.backend_record.company_id.id],
                               {'currency_id': currency_id.id})
        return {'backend_id': self.backend_record.id}


@prestashop
class TaxRuleMapper(PrestashopImportMapper):
    _model_name = 'prestashop.tax.rule'

    direct = [
        ('id_tax_rules_group', 'tax_group_id'),
        ('id_tax', 'tax_id'),
    ]

    @mapping
    def tax_id(self, record):
        tax_binder = self.get_binder_for_model('prestashop.account.tax')
        tax_id = tax_binder.to_openerp(
            record['id_tax'])
        if not tax_id:
            return {}
        if record['id_tax_rules_group']:
            p_binder_tax = self.get_connector_unit_for_model(
                Binder, 'prestashop.account.tax')
            tax = p_binder_tax.to_openerp(record['id_tax'], unwrap=True)
            p_binder_tax_group = self.get_connector_unit_for_model(
                Binder, 'prestashop.account.tax.group')
            tax_group = p_binder_tax_group.to_openerp(
                record['id_tax_rules_group'], unwrap=True)
            self.session.write(
                'account.tax',
                [tax.id],
                {'group_id': tax_group.id}
            )
        return {'tax_id': tax_id.id}

    @mapping
    def tax_group_id(self, record):
        tax_group_binder = self.get_binder_for_model(
            'prestashop.account.tax.group')
        tax_group_id = tax_group_binder.to_openerp(
            record['id_tax_rules_group'])
        if not tax_group_id:
            return {}
        return {'tax_group_id': tax_group_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class SupplierInfoMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.supplierinfo'

    direct = [
        ('product_supplier_reference', 'product_code'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def name(self, record):
        binder = self.get_connector_unit_for_model(Binder,
                                                   'prestashop.supplier')
        partner_id = binder.to_openerp(record['id_supplier'], unwrap=True)
        return {'name': partner_id.id}

    @mapping
    def product_tmpl_id(self, record):
        binder = self.get_connector_unit_for_model(
            Binder,
            'prestashop.product.template'
        )
        erp_id = binder.to_openerp(record['id_product'], unwrap=True)
        return {'product_tmpl_id': erp_id.id}

    @mapping
    def required(self, record):
        return {'min_qty': 0.0, 'delay': 1}


class PrestashopExportMapper(ExportMapper):

    def _map_direct(self, record, from_attr, to_attr):
        res = super(PrestashopExportMapper, self)._map_direct(record,
                                                              from_attr,
                                                              to_attr) or ''
        column = self.model._all_columns[from_attr].column
        if column._type == 'boolean':
            return res and 1 or 0
        elif column._type == 'float':
            res = str(res)
        return res


class TranslationPrestashopExportMapper(PrestashopExportMapper):

    def convert(self, records_by_language, fields=None):
        self.records_by_language = records_by_language
        first_key = records_by_language.keys()[0]
        self._convert(records_by_language[first_key], fields=fields)
        self._data.update(self.convert_languages(self.translatable_fields))

    def convert_languages(self, records_by_language, translatable_fields):
        res = {}
        for from_attr, to_attr in translatable_fields:
            value = {'language': []}
            for language_id, record in records_by_language.items():
                value['language'].append({
                    'attrs': {'id': str(language_id)},
                    'value': record[from_attr]
                })
            res[to_attr] = value
        return res


@prestashop
class MailMessageMapper(PrestashopImportMapper):
    _model_name = 'prestashop.mail.message'

    direct = [
        ('message', 'body'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def type(self, record):
        return {'type': 'comment'}

    @mapping
    def object_ref(self, record):
        binder = self.get_connector_unit_for_model(
            Binder, 'prestashop.sale.order'
        )
        order_id = binder.to_openerp(record['id_order'], unwrap=True)
        return {
            'model': 'sale.order',
            'res_id': order_id,
        }

    @mapping
    def author_id(self, record):
        if record['id_customer'] != '0':
            binder = self.get_connector_unit_for_model(
                Binder, 'prestashop.res.partner')
            partner_id = binder.to_openerp(record['id_customer'], unwrap=True)
            return {'author_id': partner_id}
        return {}


@prestashop
class ProductPricelistMapper(PrestashopImportMapper):
    _model_name = 'prestashop.groups.pricelist'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def static(self, record):
        return {'active': True, 'type': 'sale'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    @only_create
    def versions(self, record):
        price_disc = -float(record['reduction']) / 100.0
        item = {
            'min_quantity': 0,
            'sequence': 5,
            'base': 1,
            'price_discount': price_disc,
        }
        version = {
            'name': 'Version',
            'active': True,
            'items_id': [(0, 0, item)],
        }
        return {'version_id': [(0, 0, version)]}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
