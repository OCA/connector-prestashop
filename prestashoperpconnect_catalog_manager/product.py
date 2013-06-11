# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2013 Akretion                                               #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_create
from openerp.addons.connector.unit.mapper import ExportMapper, mapping

from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    TranslationPrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect.unit.mapper import TranslationPrestashopExportMapper
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop

@on_record_create(model_names='prestashop.product.product')
def openerp_product_created(session, model_name, record_id):
    export_record.delay(session, model_name, record_id)


@prestashop
class ProductExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.product'

@prestashop
class ProductExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.product'

    direct = [
        ('lst_price', 'price'),

#        ('description_html', 'description'),
#        ('weight', 'weight'),
#        ('standard_price', 'wholesale_price'),
#        ('default_code', 'reference'),
#        ('date_add', 'date_add'),
#        ('date_upd', 'date_upd'),
#        ('default_shop_id', 'id_shop_default'),
#        ('prestashop_id', 'id'),
    ]

    translatable_fields = [
        ('name', 'name'),
        ('link_rewrite', 'link_rewrite'),
    ]
