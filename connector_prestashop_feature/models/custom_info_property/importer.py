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
    import_batch,
    DelayedBatchImporter,
    TranslatableRecordImporter,
    import_record,
)
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.backend_adapter import \
    PrestaShopCRUDAdapter

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


@prestashop
class ProductFeaturesImporter(TranslatableRecordImporter):
    _model_name = [
        'prestashop.product.features',
    ]

    _translatable_fields = {
        'prestashop.product.features': ['name'],
    }

    def _import_feature_values(self):
        record = self._get_prestashop_data()
        feature_value_adapter = self.unit_for(
            PrestaShopCRUDAdapter,
            'prestashop.product.feature.values')
        filters = {
            'filter[id_feature]': record['id'],
        }
        feature_values = feature_value_adapter.search(filters)
        feature_value_binder = self.binder_for(
            'prestashop.product.feature.values')
        for value in feature_values:
            if not feature_value_binder.to_odoo(value):
                import_record(
                    self.session, 'prestashop.product.feature.values',
                    self.backend_record.id, value)

    def _after_import(self, binding):
        super(ProductFeaturesImporter, self)._after_import(binding)
        self._import_feature_values()


@prestashop
class ProductFeaturesImportMapper(ImportMapper):
    _model_name = 'prestashop.product.features'

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('name', 'name'),
        ('position', 'sequence'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def field_type(self, record):
        return {'field_type': 'id'}

    @mapping
    @only_create
    def assign_custom_template(self, record):
        custom_tmpl = self.env.ref(
            'connector_prestashop_feature.tpl_prestashop_features')
        return {'template_id': custom_tmpl.id}


@prestashop
class ProductFeaturesBatchImport(DelayedBatchImporter):
    """ Import the PrestaShop Product Features. """
    _model_name = 'prestashop.product.features'


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
