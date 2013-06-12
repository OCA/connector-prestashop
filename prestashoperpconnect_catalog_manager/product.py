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
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import ExportMapper, mapping

from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    TranslationPrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect.unit.mapper import TranslationPrestashopExportMapper
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.product import INVENTORY_FIELDS

@on_record_create(model_names='prestashop.product.product')
def prestashop_product_product_create(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id)

@on_record_write(model_names='prestashop.product.product')
def prestashop_product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    fields = list(set(fields).difference(set(INVENTORY_FIELDS)))
    if fields:
        export_record.delay(session, model_name, record_id, fields)

@on_record_write(model_names='product.product')
def product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                           record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.product', binding.id, fields)

@prestashop
class ProductExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.product'

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        #TODO add export of category
        return 


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

    @mapping
    def associations(self, record):
        ext_categ_ids = []
        binder = self.get_binder_for_model('prestashop.product.category')
        categ_ids = record['categ_ids'] + [record['categ_id'][0]]
        for categ_id in categ_ids:
            ext_categ_ids.append(
                    {'id' : binder.to_backend(categ_id, unwrap=True)}
                    )
        return {'associations': {'categories': {'category_id': ext_categ_ids}}}

    @mapping
    def categ_id(self, record):
        binder = self.get_binder_for_model('prestashop.product.category')
        ext_categ_id = binder.to_backend(record['categ_id'][0], unwrap=True)
        return {'id_category_default': ext_categ_id}
