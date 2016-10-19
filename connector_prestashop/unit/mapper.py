# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.unit.mapper import ExportMapper


# TODO: check if this stuff is needed for catalog export
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
