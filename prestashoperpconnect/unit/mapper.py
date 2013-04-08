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
        Returns an openerp_id from a model name and a prestashop_id.

        This function is a helper that permits to only write one line for
        mapping a foreign key.
        '''
        binder = self.get_binder_for_model(model)
        return binder.to_openerp(prestashop_id)


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
        if isinstance(groups, list):
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
        prestashop_partner_id = self.get_fk_id(
            'prestashop.res.partner',
            record['id_customer']
        )
        model = self.session.pool.get('prestashop.res.partner')
        prestashop_partner = model.read(
            self.session.cr,
            self.session.uid,
            prestashop_partner_id
        )
        return {'parent_id': prestashop_partner['openerp_id'][0]}

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
