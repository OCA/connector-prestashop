# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.connector_prestashop.connector import get_environment
from openerp.addons.connector_prestashop.unit.exporter import (
    PrestashopExporter,
    export_record,
    TranslationPrestashopExporter,
)
from openerp.addons.connector_prestashop.unit.mapper import (
    TranslationPrestashopExportMapper,
    PrestashopExportMapper
)
from openerp.addons.connector_prestashop.backend import prestashop


@prestashop
class ProductFeaturesExporter(PrestashopExporter):
    _model_name = 'prestashop.product.features'

    _translatable_fields = {
        'prestashop.product.features': ['name'],
    }

    def _create(self, record):
        res = super(ProductFeaturesExporter, self)._create(record)
        return res['prestashop']['category']['id']


@prestashop
class ProductFeaturesExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.product.features'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def position(self, record):
        return {'position': int(record['position'])}


@job(default_channel='root.prestashop')
def export_product_feature(session, model_name, record_id, fields=None):
    """ Export custom info property mapped to product features. """
    template = session.env[model_name].browse(record_id)
    backend_id = template.backend_id.id
    env = get_environment(session, model_name, backend_id)
    features_exporter = env.get_connector_unit(ProductFeaturesExporter)
    return features_exporter.run(record_id, fields)