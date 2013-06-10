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
from openerp.addons.connector.unit.mapper import ExportMapper

from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    PrestashopExporter
)
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop

@on_record_create(model_names='prestashop.product.product')
def openerp_product_created(session, model_name, record_id):
    export_product.delay(session, model_name, record_id)


@job
def export_product(session, model_name, record_id, fields=None):
    """ Export a product. """
    product = session.browse(model_name, record_id)
    backend_id = product.backend_id.id
    env = get_environment(session, model_name, backend_id)
    product_exporter = env.get_connector_unit(PrestashopExporter)
    return product_exporter.run(record_id, fields)


@prestashop
class ProductExport(PrestashopExporter):
    _model_name = 'prestashop.product.product'


@prestashop
class ProductExportMapper(ExportMapper):
    _model_name = 'prestashop.product.product'

    direct = [
        ('name','name'),
        ('description_html', 'description'),
        ('weight', 'weight'),
        ('standard_price', 'wholesale_price'),
        ('lst_price', 'price'),
        ('default_code', 'reference'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('default_shop_id', 'id_shop_default'),
    ]

