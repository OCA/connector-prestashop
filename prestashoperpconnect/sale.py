# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2013 Akretion                                               #
#   Copyright (C) 2015 Tech-Receptives(<http://www.tech-receptives.com>)      #
#   @author Parthiv Patel <parthiv@techreceptives.com>                        #
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

from prestapyt import PrestaShopWebServiceDict
from backend import prestashop
from openerp.addons.connector.event import on_record_write
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import (ExportSynchronizer)
from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)
from .connector import get_environment
from .unit.backend_adapter import GenericAdapter


ORDER_STATUS_MAPPING = {
    'draft': "Preparation in progress",
    'sent': "Preparation in progress",
    'manual': "Awaiting bank wire payment",
    'progress': "Payment accepted",
    'shipping_except': "",
    'invoice_except': "Payment error",
    'done': "Delivered",
    'cancel': "Canceled",
    'waiting_date': ""
}


@prestashop
class PrestaShopSaleOrderOnChange(SaleOrderOnChange):
    _model_name = 'prestashop.sale.order'


@prestashop
class SaleOrderStateAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.state'
    _prestashop_model = 'order_states'


@prestashop
class SaleOrderAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def update_sale_state(self, prestashop_id, datas):
        api = self.connect()
        return api.add('order_histories', datas)

    def search(self, filters=None):
        result = super(SaleOrderAdapter, self).search(filters=filters)

        shop_ids = self.session.search('prestashop.shop', [
            ('backend_id', '=', self.backend_record.id)
        ])
        shops = self.session.browse('prestashop.shop', shop_ids)
        for shop in shops:
            if not shop.default_url:
                continue

            api = PrestaShopWebServiceDict(
                '%s/api' % shop.default_url, self.prestashop.webservice_key
            )
            result += api.search(self._prestashop_model, filters)
        return result


@prestashop
class OrderCarriers(GenericAdapter):
    _model_name = '__not_exit_prestashop.order_carrier'
    _prestashop_model = 'order_carriers'
    _export_node_name = 'order_carrier'


@prestashop
class PaymentMethodAdapter(GenericAdapter):
    _model_name = 'payment.method'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def search(self, filters=None):
        api = self.connect()
        res = api.get(self._prestashop_model, options=filters)
        methods = res[self._prestashop_model][self._export_node_name]
        if isinstance(methods, dict):
            return [methods]
        return methods


@prestashop
class SaleOrderLineAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.line'
    _prestashop_model = 'order_details'


@prestashop
class SaleStateExport(ExportSynchronizer):
    _model_name = ['prestashop.sale.order']

    def run(self, prestashop_id, state):
        datas = {
            'order_history': {
                'id_order': prestashop_id,
                'id_order_state': state,
            }
        }
        self.backend_adapter.update_sale_state(prestashop_id, datas)


# TODO improve me, don't try to export state if the sale order does not come
#      from a prestashop connector
# TODO improve me, make the search on the sale order backend only
@on_record_write(model_names='sale.order')
def prestashop_sale_state_modified(session, model_name, record_id,
                                   fields=None):
    if 'state' in fields:
        sale = session.browse(model_name, record_id)
        # a quick test to see if it is worth trying to export sale state
        new_state = ORDER_STATUS_MAPPING[sale.state]
        states = session.search('sale.order.state', [('name', '=', new_state)])
        if states:
            export_sale_state.delay(session, record_id, priority=20)
    return True


@job
def export_sale_state(session, record_id):
    inherit_model = 'prestashop.sale.order'
    sale_ids = session.search(inherit_model, [('openerp_id', '=', record_id)])
    if not isinstance(sale_ids, list):
        sale_ids = [sale_ids]
    for sale in session.browse(inherit_model, sale_ids):
        backend_id = sale.backend_id.id
        new_state = ORDER_STATUS_MAPPING[sale.state]
        state_ids = session.search(
            'sale.order.state', [('name', '=', new_state)])
        prestashop_state_ids = session.search(
            'prestashop.sale.order.state', [('openerp_id', '=', state_ids[0])])
        prestashop_state = session.browse(
            'prestashop.sale.order.state', prestashop_state_ids[0])
        env = get_environment(session, inherit_model, backend_id)
        sale_exporter = env.get_connector_unit(SaleStateExport)
        if prestashop_state:
            sale_exporter.run(
                sale.prestashop_id, prestashop_state.prestashop_id)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
