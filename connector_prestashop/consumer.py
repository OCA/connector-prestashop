# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.connector.event import on_record_write
from odoo.addons.connector_ecommerce.models.event import (
    on_tracking_number_added,
)
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
        env, model_name, record_id, fields=None):
    if env.context.get('connector_no_export'):
        return
    inventory_fields = list(set(fields).intersection(INVENTORY_FIELDS))
    if inventory_fields:
        env[model_name].browse(record_id).with_delay(
            priority=20).export_inventory(fields=inventory_fields)


@on_record_write(model_names='sale.order')
def prestashop_sale_state_modified(env, model_name, record_id,
                                   fields=None):
    if 'state' in fields:
        sale = env[model_name].browse(record_id)
        if not sale.prestashop_bind_ids:
            return
        # a quick test to see if it is worth trying to export sale state
        states = env['sale.order.state.list'].search(
            [('name', '=', sale.state)]
        )
        if states:
            export_sale_state.delay(env, 'prestashop.sale.order',
                                    record_id, priority=20)


@on_tracking_number_added
def delay_export_tracking_number(env, model_name, record_id):
    """
    Call a job to export the tracking number to a existing picking that
    must be in done state.
    """
    picking = env['stock.picking'].browse(record_id)
    for binding in picking.sale_id.prestashop_bind_ids:
        export_tracking_number.delay(env,
                                     binding._model._name,
                                     binding.id,
                                     priority=20)
