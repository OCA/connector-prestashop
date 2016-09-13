# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.addons.connector.event import on_record_write
from openerp.addons.connector_ecommerce.models.event import (
    on_tracking_number_added,
)
from .models.product_template.exporter import export_inventory
from .models.sale_order_state.exporter import export_sale_state
from .models.stock_tracking.exporter import export_tracking_number

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

@on_record_write(model_names=[
    'prestashop.product.template',
    'prestashop.product.combination'
])
def prestashop_product_stock_updated(
        session, model_name, record_id, fields=None):
    if session.env.context.get('connector_no_export'):
        return
    inventory_fields = list(set(fields).intersection(INVENTORY_FIELDS))
    if inventory_fields:
        export_inventory.delay(session, model_name,
                               record_id, fields=inventory_fields,
                               priority=20)


@on_record_write(model_names='sale.order')
def prestashop_sale_state_modified(session, model_name, record_id,
                                   fields=None):
    if 'state' in fields:
        sale = session.env[model_name].browse(record_id)
        if not sale.prestashop_bind_ids:
            return
        # a quick test to see if it is worth trying to export sale state
        states = session.env['sale.order.state.list'].search(
            [('name', '=', sale.state)]
        )
        if states:
            export_sale_state.delay(session, 'prestashop.sale.order',
                                    record_id, priority=20)


@on_tracking_number_added
def delay_export_tracking_number(session, model_name, record_id):
    """
    Call a job to export the tracking number to a existing picking that
    must be in done state.
    """
    picking = session.env['stock.picking'].browse(record_id)
    for binding in picking.sale_id.prestashop_bind_ids:
        export_tracking_number.delay(session,
                                     binding._model._name,
                                     binding.id,
                                     priority=20)
