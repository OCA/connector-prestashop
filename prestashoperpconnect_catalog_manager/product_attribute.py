# -*- coding: utf-8 -*-
###############################################################################
#
#   Prestashop_catalog_manager for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>. All Rights Reserved
#   @author : Sébastien BEAU <sebastien.beau@akretion.com>
#             Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import fields, orm
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    export_record,
    TranslationPrestashopExporter,
    )
from openerp.addons.prestashoperpconnect.unit.binder import PrestashopModelBinder
from openerp.addons.prestashoperpconnect.unit.mapper import TranslationPrestashopExportMapper
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter
from openerp.addons.connector.exception import InvalidDataError
from openerp.addons.connector.unit.mapper import mapping


class product_attribute(orm.Model):
    _inherit = 'product.attribute'

    _columns ={
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.attribute',
            'openerp_id',
            string="PrestaShop Bindings"
        ),
    }


class prestashop_product_attribute(orm.Model):
    _name = 'prestashop.product.attribute'
    _inherit = 'prestashop.binding'
    _inherits = {'product.attribute': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.attribute',
            string='Product Attribute',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_position': fields.integer(
            'Prestashop Position'),
    }

    #has to be different than 0 because of prestashop
    _defaults = {
        'prestashop_position' : 1
    }


class attribute_option(orm.Model):
    _inherit = 'attribute.option'

    _columns ={
        'prestashop_bind_ids': fields.one2many(
            'prestashop.attribute.option',
            'openerp_id',
            string="PrestaShop Bindings"
        ),
    }


class prestashop_attribute_option(orm.Model):
    _name = 'prestashop.attribute.option'
    _inherit = 'prestashop.binding'
    _inherits = {'attribute.option': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'attribute.option',
            string='Attribute Option',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_product_attribute_id': fields.many2one(
            'prestashop.product.attribute',
            string='Prestashop Product Attribute',
            required=True,
            ondelete='cascade'
        )
    }

    def create(self, cr, uid, vals, context=None):
        prest_attribute_obj = self.pool['prestashop.product.attribute']
        attribute_option_obj = self.pool['attribute.option']
        option = attribute_option_obj.read(cr, uid, vals['openerp_id'],
                                           ['attribute_id'], context=context)
        if option and option['attribute_id']:
            prestashop_attribute_ids = prest_attribute_obj.search(
                cr, uid, [('backend_id', '=', vals['backend_id']),
                          ('openerp_id', '=', option['attribute_id'][0])],
                context=context)
            if prestashop_attribute_ids:
                vals['prestashop_product_attribute_id'] = prestashop_attribute_ids[0]
                return super(prestashop_attribute_option, self).create(
                    cr, uid, vals, context=context)
        raise InvalidDataError("You have to export the product attribute before "
                               "the attribute option !")
        return True


@on_record_create(model_names='prestashop.product.attribute')
def prestashop_product_attribute_created(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id)


@on_record_create(model_names='prestashop.attribute.option')
def prestashop_attribute_option_created(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id)

@on_record_write(model_names='prestashop.product.attribute')
def prestashop_product_attribute_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id)

@on_record_write(model_names='prestashop.attribute.option')
def prestashop_attribute_option_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id)

@on_record_write(model_names='product.attribute')
def product_attribute_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                           record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.attribute', binding.id, fields)

@on_record_write(model_names='attribute.option')
def attribute_option_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                           record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.attribute.option', binding.id, fields)


@prestashop
class ProductAttributeAdapter(GenericAdapter):
    _model_name = 'prestashop.product.attribute'
    _prestashop_model = 'product_features'
    _export_node_name = 'product_feature'


@prestashop
class AttributeOptionAdapter(GenericAdapter):
    _model_name = 'prestashop.attribute.option'
    _prestashop_model = 'product_feature_values'
    _export_node_name = 'product_feature_value'


@prestashop
class PrestashopProductAttributeBinder(PrestashopModelBinder):
    _model_name = 'prestashop.product.attribute'


@prestashop
class PrestashopAttributeOptionBinder(PrestashopModelBinder):
    _model_name = 'prestashop.attribute.option'


@prestashop
class ProductAttributeExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.attribute'


@prestashop
class AttributeOptionExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.attribute.option'

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        prest_attribute_id = self.erp_record.prestashop_product_attribute_id.id
        # export product attribute
        binder = self.get_binder_for_model('prestashop.product.attribute')
        if not binder.to_backend(prest_attribute_id):
            exporter = self.get_connector_unit_for_model(TranslationPrestashopExporter,
                                                         'prestashop.product.attribute')
            exporter.run(prest_attribute_id)
        return


@prestashop
class ProductAttributeExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.attribute'

    direct = [
        ('prestashop_position', 'position'),
    ]

    translatable_fields = [
        ('field_description', 'name'),
    ]


@prestashop
class AttributeOptionExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.attribute.option'

    direct = []

    @mapping
    def prestashop_product_attribute_id(self, record):
        return {'id_feature': record.prestashop_product_attribute_id.prestashop_id}

    translatable_fields = [
        ('name', 'value'),
    ]
