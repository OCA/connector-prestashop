# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.addons.connector.event import (
    on_record_create,
    on_record_write,
)
# from openerp.addons.connector_prestashop.unit.exporter import export_record
from .models.res_partner.exporter import export_manufacturer


@on_record_create(model_names='res.partner')
@on_record_write(model_names='res.partner')
def prestashop_manufacturer(session, model_name, record_id, fields):
    """Sync partner as manufacturer.

    Sync happens only if:
    * partner type is "supplier"
    * PS manufacturer category is applied to it
    """
    if session.context.get('connector_no_export'):
        return
    record = session.env[model_name].browse(record_id)
    ps_categ = session.env.ref(
        'connector_prestashop_manufacturer.partner_manufacturer_tag')
    if record.supplier and ps_categ.id in record.category_id.ids:
        export_manufacturer.delay(session, record_id, priority=20)
