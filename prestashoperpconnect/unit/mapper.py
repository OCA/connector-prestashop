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
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper)
from ..backend import prestashop


class PrestashopImportMapper(ImportMapper):

    _fk_mapping = [
        # (model_name, record_key, return_key)
    ]

    @mapping
    def _get_fk_mapping(self, record):
        mapping_values = {}
        for model_name, record_key, return_key in self._fk_mapping:
            fk_id = self.get_fk_id(model_name, record[record_key])
            mapping_values[return_key] = fk_id
        return mapping_values

    def get_fk_id(self, model, prestashop_id):
        '''
        Returns a prestashop.* id from a model name and a prestashop_id.

        This function is a helper that permits to only write one line for
        mapping a foreign key.
        '''
        binder = self.get_binder_for_model(model)
        return binder.to_openerp(prestashop_id)

    def get_openerp_id(self, model, prestashop_id):
        '''
        Returns an openerp id from a model name and a prestashop_id.

        This permits to find the openerp id through the prestahop model in
        openerp.
        '''
        oerp_ps_id = self.get_fk_id(model, prestashop_id)
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

    direct = [('name', 'name')]

    _fk_mapping = [
        ('prestashop.shop.group', 'id_shop_group', 'shop_group_id')
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
    ]

    _fk_mapping = [
        ('prestashop.shop.group', 'id_shop_group', 'shop_group_id'),
        ('prestashop.shop', 'id_shop', 'shop_id'),
        (
            'prestashop.res.partner.category',
            'id_default_group',
            'default_category_id'
        ),
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
        oerp_lang_id = self.get_fk_id('prestashop.res.lang', record['id_lang'])

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
    ]

    _fk_mapping = [
        ('prestashop.res.partner', 'id_customer', 'prestashop_partner_id'),
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

    _fk_mapping = [
        ('prestashop.shop', 'id_shop_default', 'default_shop_id'),
    ]

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
        ('available_for_sale', 'sale_ok'),
        ('wholesale_price', 'standard_price'),
        ('price', 'lst_price'),
        ('reference', 'default_code'),
    ]

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
