# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector_prestashop.unit.exporter import (
    export_record,
    PrestashopExporter,
    TranslationPrestashopExporter,
)
from openerp.addons.connector_prestashop.unit.mapper import \
    TranslationPrestashopExportMapper
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector.unit.mapper import mapping


@on_record_create(model_names='prestashop.product.combination.option')
def prestashop_product_attribute_created(
        session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_create(model_names='prestashop.product.combination.option.value')
def prestashop_product_atrribute_value_created(
        session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.combination.option')
def prestashop_product_attribute_written(session, model_name, record_id,
                                         fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.combination.option.value')
def prestashop_attribute_option_written(session, model_name, record_id,
                                        fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='product.attribute.value')
def product_attribute_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.combination.option',
                            binding.id, fields, priority=20)


@on_record_write(model_names='produc.attribute.value')
def attribute_option_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session,
                            'prestashop.product.combination.option.value',
                            binding.id, fields, priority=20)


@prestashop
class ProductCombinationOptionExport(PrestashopExporter):
    _model_name = 'prestashop.product.combination.option'

    def _create(self, record):
        res = super(ProductCombinationOptionExport, self)._create(record)
        return res['prestashop']['product_option']['id']


@prestashop
class ProductCombinationOptionExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.combination.option'

    direct = [
        ('prestashop_position', 'position'),
        ('group_type', 'group_type'),
    ]

    @mapping
    def translatable_fields(self, record):
        translatable_fields = [
            ('name', 'name'),
            ('name', 'public_name'),
        ]
        trans = TranslationPrestashopExporter(self.connector_env)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields


@prestashop
class ProductCombinationOptionValueExport(PrestashopExporter):
    _model_name = 'prestashop.product.combination.option.value'

    def _create(self, record):
        res = super(ProductCombinationOptionValueExport, self)._create(record)
        return res['prestashop']['product_option_value']['id']

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        attribute_id = self.erp_record.attribute_id.id
        # export product attribute
        binder = self.binder_for('prestashop.product.combination.option')
        if not binder.to_backend(attribute_id, wrap=True):
            exporter = self.get_connector_unit_for_model(
                TranslationPrestashopExporter,
                'prestashop.product.combination.option')
            exporter.run(attribute_id)
        return


@prestashop
class ProductCombinationOptionValueExportMapper(
        TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.combination.option.value'

    direct = [('name', 'value')]

    @mapping
    def prestashop_product_attribute_id(self, record):
        attribute_binder = self.binder_for(
            'prestashop.product.combination.option.value')
        return {
            'id_feature': attribute_binder.to_backend(
                record.attribute_id.id, wrap=True)
        }

    @mapping
    def prestashop_product_group_attribute_id(self, record):
        attribute_binder = self.binder_for(
            'prestashop.product.combination.option')
        return {
            'id_attribute_group': attribute_binder.to_backend(
                record.attribute_id.id, wrap=True),
        }

    @mapping
    def translatable_fields(self, record):
        translatable_fields = [
            ('name', 'name'),
        ]
        trans = TranslationPrestashopExporter(self.connector_env)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields
