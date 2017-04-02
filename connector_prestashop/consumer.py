# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.event import on_record_write
from openerp.addons.connector_ecommerce.event import on_tracking_number_added
from .unit.deleter import export_delete_record
from .connector import get_environment
from .unit.binder import PrestashopBinder
from .unit.exporter import export_record
from .models.product_template.exporter import export_inventory
from .models.sale_order_state.exporter import export_sale_state
from .models.stock_tracking.exporter import export_tracking_number

# fields which should not trigger an export of the products
# but an export of their inventory
INVENTORY_FIELDS = ('quantity',)


@on_record_write(model_names=[
    'prestashop.product.template',
    'prestashop.product.combination'
])
def prestashop_product_stock_updated(
        session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    inventory_fields = list(set(fields).intersection(INVENTORY_FIELDS))
    if inventory_fields:
        export_inventory.delay(session, model_name,
                               record_id, fields=inventory_fields,
                               priority=20)


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
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    env = get_environment(session, model_name, record.backend_id.id)
    binder = env.get_connector_unit(PrestashopBinder)
    external_id = binder.to_backend(record_id)
    if external_id:
        export_delete_record.delay(session, model_name,
                                   record.backend_id.id, external_id,
                                   priority=priority)


def delay_unlink_all_bindings(session, model_name, record_id, priority=20):
    """ Delay a job which delete a record on PrestaShop.

    Called on binding records."""
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for bind_record in record.prestashop_bind_ids:
        prestashop_model_name = bind_record._name
        env = get_environment(
            session, prestashop_model_name, bind_record.backend_id.id)
        binder = env.get_connector_unit(PrestashopBinder)
        ext_id = binder.to_backend(bind_record.id)
        if ext_id:
            export_delete_record.delay(
                session, prestashop_model_name,
                bind_record.backend_id.id, ext_id, priority=priority)


# TODO improve me, don't try to export state if the sale order does not come
#      from a prestashop connector
# TODO improve me, make the search on the sale order backend only
@on_record_write(model_names='sale.order')
def prestashop_sale_state_modified(session, model_name, record_id,
                                   fields=None):
    if 'state' in fields:
        sale = session.env[model_name].browse(record_id)
        # a quick test to see if it is worth trying to export sale state
        states = session.env['sale.order.state.list'].search([
            ('name', '=', sale.state),
        ])
        if states:
            export_sale_state.delay(session, record_id, priority=20)
    return True


@on_tracking_number_added
def delay_export_tracking_number(session, model_name, record_id):
    """
    Call a job to export the tracking number to a existing picking that
    must be in done state.
    """
    # browse on stock.picking because we cant read on stock.picking.out
    # buggy virtual models... Anyway the ID is the same
    picking = session.browse('stock.picking', record_id)
    for binding in picking.sale_id.prestashop_bind_ids:
        export_tracking_number.delay(session,
                                     binding._model._name,
                                     binding.id,
                                     priority=20)
