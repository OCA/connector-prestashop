# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.unit.mapper import mapping


class PrestashopImportMapper(AbstractComponent):
    _name = 'prestashop.import.mapper'
    _inherit = ['base.prestashop.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class PrestashopExportMapper(AbstractComponent):
    _name = 'prestashop.export.mapper'
    _inherit = ['base.prestashop.connector', 'base.export.mapper']
    _usage = 'export.mapper'

    def _map_direct(self, record, from_attr, to_attr):
        res = super(PrestashopExportMapper, self)._map_direct(record,
                                                              from_attr,
                                                              to_attr) or ''
        if isinstance(from_attr, basestring):
            column = self.model._all_columns[from_attr].column
            if column._type == 'boolean':
                return res and 1 or 0
            elif column._type == 'float':
                res = str(res)
        return res


class TranslationPrestashopExportMapper(AbstractComponent):
    _name = 'translation.prestashop.export.mapper'
    _inherit = 'prestashop.export.mapper'

    @mapping
    def translatable_fields(self, record):
        fields = getattr(self, '_translatable_fields', [])
        if fields:
            translated_fields = self._convert_languages(
                self._get_record_by_lang(record), fields)
            return translated_fields
        return {}

    def _get_record_by_lang(self, record):
        # get the backend's languages
        languages = self.backend_record.language_ids
        records = {}
        # for each languages:
        for language in languages:
            # get the translated record
            record = record.with_context(
                lang=language['code'])
            # put it in the dict
            records[language['prestashop_id']] = record
        return records

    def _convert_languages(self, records_by_language, translatable_fields):
        res = {}
        for from_attr, to_attr in translatable_fields:
            value = {'language': []}
            for language_id, record in records_by_language.iteritems():
                value['language'].append({
                    'attrs': {'id': str(language_id)},
                    'value': record[from_attr] or ''
                })
            res[to_attr] = value
        return res
