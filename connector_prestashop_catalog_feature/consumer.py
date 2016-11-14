# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.addons.connector.event import on_record_write, on_record_create
from openerp.addons.connector_prestashop.unit.exporter import export_record


@on_record_write(model_names='prestashop.product.features')
def prestashop_product_features_updated(
        session, model_name, record_id, fields=None):
    if session.env.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name,record_id)


@on_record_create(model_names='prestashop.product.features')
def prestashop_product_featres_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.feature.values')
def prestashop_product_features_updated(
        session, model_name, record_id, fields=None):
    if session.env.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name,record_id)


@on_record_create(model_names='prestashop.product.feature.values')
def prestashop_product_featres_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='custom.info.option')
def custum_info_option(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if session.env.ref('connector_prestashop_feature.tpl_prestashop_features'):
        model = session.env[model_name]
        record = model.browse(record_id)
        for binding in record.prestashop_bind_ids:
            export_record.delay(session, binding._model._name, binding.id,
                                fields=fields, priority=20)
