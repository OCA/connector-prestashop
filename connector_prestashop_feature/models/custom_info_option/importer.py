# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import (
    ImportMapper,
    mapping,
)
from openerp.addons.connector_prestashop.unit.importer import (
    import_batch,
    DelayedBatchImporter,
    TranslatableRecordImporter,
)
from openerp.addons.connector_prestashop.backend import prestashop

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


@prestashop
class ProductFeatureValuesImporter(TranslatableRecordImporter):
    _model_name = [
        'prestashop.product.feature.values',
    ]

    _translatable_fields = {
        'prestashop.product.feature.values': ['value'],
    }

    def _import_feature(self):
        record = self.prestashop_record
        if int(record['id_feature']):
            self._import_dependency(
                record['id_feature'], 'prestashop.product.features')

    def _import_dependencies(self):
        super(ProductFeatureValuesImporter, self)._import_dependencies()
        # self._import_feature()


@prestashop
class ProductFeatureValuesImportMapper(ImportMapper):
    _model_name = 'prestashop.product.feature.values'

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('value', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def feature_mapper(self, record):
        binder = self.binder_for('prestashop.product.features')
        feature = binder.to_odoo(record['id_feature'], unwrap=True)
        return {'property_ids': [(4, feature.id)]}


@prestashop
class ProductFeatureValuesBatchImport(DelayedBatchImporter):
    """ Import the PrestaShop Product Feature Values. """
    _model_name = 'prestashop.product.feature.values'


@job(default_channel='root.prestashop')
def import_product_features(session, backend_id, since_date):
    filters = None
    if since_date:
        filters = {'date': '1',
                   'filter[date_upd]': '>[%s]' % since_date}
    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    import_batch(session, 'prestashop.product.features', backend_id, filters)
    session.env['prestashop.backend'].browse(backend_id).write({
        'import_product_features_since': now_fmt
    })
