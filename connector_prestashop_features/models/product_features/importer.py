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
    TranslatableRecordImporter,
    import_record,
)
from openerp.addons.connector_prestashop.backend import prestashop

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
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get('product_features', {})

        ps_key = self.backend_record.get_version_ps_key('product_features')
        features = associations.get('product_features', {}).get(ps_key, [])

        if not isinstance(features, list):
            features = [features]
        if features:
            for feature in features:
                import_record(
                    self.session, 'prestashop.product.feature.values',
                    self.backend_record.id, feature['id'])

    def _after_import(self, binding):
        super(ProductFeaturesImporter, self)._after_import(binding)
        self._import_feature_values()
        

@prestashop
class ProductFeaturesImportMapper(ImportMapper):
    _model_name = 'prestashop.product.features'

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
        return {'position': int(record['position'])}

    @mapping
    def field_type(self, record):
        return {'field_type': 'id'}

    @mapping
    @only_create
    def assign_custom_template(self, record):
        custom_tmpl = self.env.ref(
            'connector_prestashop_features.tpl_prestashop_features')
        return {'template_id': custom_tmpl.id}


@prestashop
class ProductFeaturesBatchImport(DelayedBatchImporter):
    """ Import the PrestaShop Product Features. """
    _model_name = 'prestashop.product.features'


@prestashop
class ProductFeatureValuesImporter(TranslatableRecordImporter):
    _model_name = [
        'prestashop.product.feature.values',
    ]
    
    _translatable_fields = {
        'prestashop.product.feature.values': ['name'],
    }
    
    def _import_feature(self):
        
        record = self.prestashop_record
        if int(record['id']):
            self._import_dependency(
                record['id'], 'prestashop.product.features')
    
    def _import_dependencies(self):
        super(ProductFeatureValuesImporter, self)._import_dependencies()
        self._import_feature()


@prestashop
class ProductFeatureValuesImportMapper(ImportMapper):
    _model_name = 'prestashop.product.feature.values'

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
    def property(self, record):
        return {'property_ids': [(4, id)]}

    @mapping
    def property(self, record):
        # Field property_ids
        return {}


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
