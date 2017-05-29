# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper)
from odoo.addons.connector.unit.mapper import external_to_m2o
from ...unit.importer import TranslatableRecordImporter, DelayedBatchImporter
from ...backend import prestashop

import datetime
import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


@prestashop
class ProductCategoryMapper(ImportMapper):
    _model_name = 'prestashop.product.category'

    direct = [
        ('description', 'description'),
        ('link_rewrite', 'link_rewrite'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('meta_title', 'meta_title'),
        (external_to_m2o('id_shop_default'), 'default_shop_id'),
        ('active', 'active'),
        ('position', 'position')
    ]

    @mapping
    def name(self, record):
        if record['name'] is None:
            return {'name': ''}
        return {'name': record['name']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        if record['id_parent'] == '0':
            return {}
        category = self.binder_for('prestashop.product.category').to_internal(
            record['id_parent'], unwrap=True)
        return {
            'parent_id': category.id,
        }

    @mapping
    def data_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date_add': datetime.datetime.now()}
        return {'date_add': record['date_add']}

    @mapping
    def data_upd(self, record):
        if record['date_upd'] == '0000-00-00 00:00:00':
            return {'date_upd': datetime.datetime.now()}
        return {'date_upd': record['date_upd']}


@prestashop
class ProductCategoryImporter(TranslatableRecordImporter):
    _model_name = [
        'prestashop.product.category',
    ]

    _translatable_fields = {
        'prestashop.product.category': [
            'name',
            'description',
            'link_rewrite',
            'meta_description',
            'meta_keywords',
            'meta_title'
        ],
    }

    def _import_dependencies(self):
        record = self.prestashop_record
        if record['id_parent'] != '0':
            try:
                self._import_dependency(record['id_parent'],
                                        'prestashop.product.category')
            except PrestaShopWebServiceError, e:
                msg = _(
                    'Parent category for `%s` '
                    'cannot be imported. '
                    'Error: %s'
                )
                binder = self.binder_for()
                category = binder.to_internal(record['id'])
                if category:
                    name = category.name
                else:
                    # not imported yet, retrieve name in default lang
                    values = self._split_per_language(
                        record, fields=['name', ])
                    name = values[self._default_language]['name']

                self.backend_record.add_checkpoint(
                    model=category._name,
                    record_id=category.id,
                    message=msg % (name, str(e))
                )


@prestashop
class ProductCategoryBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.product.category'
