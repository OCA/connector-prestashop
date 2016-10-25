# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import (
    ImportMapper,
    mapping,
    only_create,
)
from openerp.addons.connector_prestashop.unit.importer import (
    PrestashopImporter,
    import_batch,
    DelayedBatchImporter,
)
from openerp.addons.connector_prestashop.backend import prestashop

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


@prestashop
class ManufacturerImporter(PrestashopImporter):
    _model_name = 'prestashop.manufacturer'


@prestashop
class ManufacturerImportMapper(ImportMapper):
    _model_name = 'prestashop.manufacturer'

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('name', 'name_ext'),
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def active(self, record):
        return {'active_ext': record['active'] == '1'}

    @mapping
    @only_create
    def assign_partner_category(self, record):
        manufacturer_categ = self.env.ref(
            'connector_prestashop_manufacturer.partner_manufacturer_tag')
        return {'category_id': [(4, manufacturer_categ.id)]}


@prestashop
class ManufacturerBatchImport(DelayedBatchImporter):
    """ Import the PrestaShop Manufacturers. """
    _model_name = 'prestashop.manufacturer'


@job(default_channel='root.prestashop')
def import_manufacturers(session, backend_id, since_date):
    filters = None
    if since_date:
        filters = {'date': '1',
                   'filter[date_upd]': '>[%s]' % since_date}
    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    import_batch(session, 'prestashop.manufacturer', backend_id, filters)
    session.env['prestashop.backend'].browse(backend_id).write({
        'import_manufacturers_since': now_fmt
    })
