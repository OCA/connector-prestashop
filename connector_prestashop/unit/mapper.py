# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import models

from openerp.addons.connector.unit.mapper import ExportMapper
from openerp.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)

# to be used until the one in OCA/connector is fixed, the issue being
# that it returns a recordset instead of an id
# see https://github.com/OCA/connector/pull/194


def backend_to_m2o(field, binding=None):
    """ A modifier intended to be used on the ``direct`` mappings.

    For a field from a backend which is an ID, search the corresponding
    binding in OpenERP and returns its ID.

    When the field's relation is not a binding (i.e. it does not point to
    something like ``magento.*``), the binding model needs to be provided
    in the ``binding`` keyword argument.

    Example::

        direct = [(backend_to_m2o('country', binding='magento.res.country'),
                   'country_id'),
                  (backend_to_m2o('country'), 'magento_country_id')]

    :param field: name of the source field in the record
    :param binding: name of the binding model is the relation is not a binding
    """
    def modifier(self, record, to_attr):
        if not record[field] or not int(record[field]):
            return False
        column = self.model._fields[to_attr]
        if column.type != 'many2one':
            raise ValueError('The column %s should be a Many2one, got %s' %
                             (to_attr, type(column)))
        rel_id = record[field]
        if binding is None:
            binding_model = column.comodel_name
        else:
            binding_model = binding
        binder = self.binder_for(binding_model)
        # if we want the normal record, not a binding,
        # we ask to the binder to unwrap the binding
        unwrap = bool(binding)
        with self.session.change_context(active_test=False):
            record = binder.to_openerp(rel_id, unwrap=unwrap)
        if not record:
            raise MappingError("Can not find an existing %s for external "
                               "record %s %s unwrapping" %
                               (binding_model, rel_id,
                                'with' if unwrap else 'without'))
        if isinstance(record, models.BaseModel):
            return record.id
        else:
            _logger.debug(
                'Binder for %s returned an id, '
                'returning a record should be preferred.', binding_model
            )
            return record
    return modifier


class PrestashopExportMapper(ExportMapper):

    def _map_direct(self, record, from_attr, to_attr):
        res = super(PrestashopExportMapper, self)._map_direct(record,
                                                              from_attr,
                                                              to_attr) or ''
        column = self.model._all_columns[from_attr].column
        if column._type == 'boolean':
            return res and 1 or 0
        elif column._type == 'float':
            res = str(res)
        return res


class TranslationPrestashopExportMapper(PrestashopExportMapper):

    def convert(self, records_by_language, fields=None):
        self.records_by_language = records_by_language
        first_key = records_by_language.keys()[0]
        self._convert(records_by_language[first_key], fields=fields)
        self._data.update(self.convert_languages(self.translatable_fields))

    def convert_languages(self, records_by_language, translatable_fields):
        res = {}
        for from_attr, to_attr in translatable_fields:
            value = {'language': []}
            for language_id, record in records_by_language.items():
                value['language'].append({
                    'attrs': {'id': str(language_id)},
                    'value': record[from_attr] or ''
                })
            res[to_attr] = value
        return res
