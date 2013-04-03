# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright (C) 2013 Camptocamp SA
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author: Guewen Baconnier
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from functools import wraps

import openerp.addons.connector as connector

from openerp.addons.connector.event import (
    on_record_write,
    on_record_create,
    on_record_unlink
    )
from openerp.addons.connector.connector import Environment

#from openerp.addons.connector_ecommerce.event import on_picking_done
#from .unit.export_synchronizer import export_record, export_picking_done
#from .unit.delete_synchronizer import export_delete_record

_MODEL_NAMES = ('res.partner',)
_BIND_MODEL_NAMES = ('prestashop.res.partner',)


def prestashop_consumer(func):
    """ Use this decorator on all the consumers of prestashoperpconnect.

    It will prevent the consumers from being fired when the prestashoperpconnect
    addon is not installed.
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        session = args[0]
        if session.pool.get('prestashoperpconnect.installed'):
            return func(*args, **kwargs)

    return wrapped


#@on_record_create(model_names=_BIND_MODEL_NAMES)
#@on_record_write(model_names=_BIND_MODEL_NAMES)
#@prestashop_consumer
#def delay_export(session, model_name, record_id, fields=None):
#    if session.context.get('connector_no_export'):
#        return
#    export_record.delay(session, model_name, record_id, fields=fields)


#@on_record_write(model_names=_MODEL_NAMES)
#@prestashop_consumer
#def delay_export_all_bindings(session, model_name, record_id, fields=None):
#    if session.context.get('connector_no_export'):
#        return
#    model = session.pool.get(model_name)
#    record = model.browse(session.cr, session.uid,
#                          record_id, context=session.context)
#    for binding in record.prestashop_bind_ids:
#        export_record.delay(session, binding._model._name, binding.id,
#                            fields=fields)


#@on_record_unlink(model_names=_BIND_MODEL_NAMES)
#@prestashop_consumer
#def delay_unlink(session, model_name, record_id):
#    model = session.pool.get(model_name)
#    record = model.browse(session.cr, session.uid,
#                          record_id, context=session.context)
#    env = Environment(record.backend_id, session, model_name)
#    binder = env.get_connector_unit(connector.connector.Binder)
#    prestashop_id = binder.to_backend(record_id)
#    if prestashop_id:
#        export_delete_record.delay(session, model_name,
#                                   record.backend_id.id, prestashop_id)


