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
import openerp.addons.connector as connector
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  ImportMapper,
                                                  ExportMapper)
from ..backend import prestashop

import types

class PrestashopImportMapper(ImportMapper):

    _fk_mapping = [
    #    (model_name, record_key, return_key)
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

        This function is a helper that permits to only write one line for mapping a
        foreign key.
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
        ('date_add','date_add'),
        ('date_upd','date_upd'),
        ('email','email'),
        ('newsletter','newsletter'),
        ('birthday','birthday'),
        ('company','company'),
        ('active', 'active'),
        ('note', 'comment'),
    ]
    
    _fk_mapping = [
       ('prestashop.shop.group', 'id_shop_group', 'shop_group_id'),
       ('prestashop.res.partner.category','id_default_group','default_category_id'),
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
        return {'name':name}

    @mapping
    def groups(self, record):
        groups = record['associations']['groups']['group']
        if type(groups) is not types.ListType:
            groups = [groups]
        partner_categories = []
        for group in groups:
            category_id = self.get_fk_id(
                'prestashop.res.partner.category',
                group['id']
            )
            partner_categories.append(category_id)

        return {'group_ids':partner_categories}

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
        return {'lang':oerp_lang['code']}
