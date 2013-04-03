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


@prestashop
class ShopGroupImportMapper(ImportMapper):
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
class ShopImportMapper(ImportMapper):
    _model_name = 'prestashop.shop'

    direct = [('name', 'name')]

    # lien vers le groupe + root category

    @mapping
    def shop_group_id(self, record):
        binder = self.get_binder_for_model('prestashop.shop.group')
        openerp_id = binder.to_openerp(record['id_shop_group'])
        return {'shop_group_id': openerp_id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class PartnerCategoryImportMapper(ImportMapper):
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

