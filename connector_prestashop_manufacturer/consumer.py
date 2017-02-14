# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


# from openerp.addons.connector.event import (
#     on_record_create,
#     on_record_write,
# )
# from openerp.addons.connector_prestashop.unit.exporter import export_record


# TODO
# @on_record_create(model_names='res.partner')
# @on_record_write(model_names='res.partner')
# def prestashop_manufacturer(session, model_name, record_id, fields):
#     if session.context.get('connector_no_export'):
#         return
#     import pdb; pdb.set_trace()
#     export_record.delay(session, 'prestashop.manufacturer',
#                         record_id, priority=20)
