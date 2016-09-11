# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.connector import Binder
from .unit.delete_synchronizer import export_delete_record
from .connector import get_environment
from .unit.export_synchronizer import export_record


def delay_export(session, model_name, record_id, fields=None, priority=20):
    """ Delay a job which export a binding record.

    (A binding record being a ``external.res.partner``,
    ``external.product.product``, ...)
    """
    if session.context.get('connector_no_export'):
        return
    export_record.delay(
        session, model_name, record_id, fields=fields, priority=priority)


def delay_export_all_bindings(
        session, model_name, record_id, fields=None, priority=20):
    """ Delay a job which export all the bindings of a record.

    In this case, it is called on records of normal models and will delay
    the export for all the bindings.
    """
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, binding._model._name, binding.id,
                            fields=fields, priority=priority)


def delay_unlink(session, model_name, record_id, priority=20):
    """ Delay a job which delete a record on PrestaShop.

    Called on binding records."""
    model = session.env[model_name]
    record = model.browse(record_id)
    env = get_environment(session, model_name, record.backend_id.id)
    binder = env.get_connector_unit(Binder)
    external_id = binder.to_backend(record_id)
    if external_id:
        export_delete_record.delay(session, model_name,
                                   record.backend_id.id, external_id,
                                   priority=priority)


def delay_unlink_all_bindings(session, model_name, record_id, priority=20):
    """ Delay a job which delete a record on PrestaShop.

    Called on binding records."""
    model = session.env[model_name]
    record = model.browse(record_id)
    for bind_record in record.prestashop_bind_ids:
        prestashop_model_name = bind_record._name
        env = get_environment(
            session, prestashop_model_name, bind_record.backend_id.id)
        binder = env.get_connector_unit(Binder)
        ext_id = binder.to_backend(bind_record.id)
        if ext_id:
            export_delete_record.delay(
                session, prestashop_model_name,
                bind_record.backend_id.id, ext_id, priority=priority)
