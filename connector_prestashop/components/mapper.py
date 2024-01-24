# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping


class PrestashopImportMapper(AbstractComponent):
    _name = "prestashop.import.mapper"
    _inherit = ["base.prestashop.connector", "base.import.mapper"]
    _usage = "import.mapper"

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}


class PrestashopExportMapper(AbstractComponent):
    _name = "prestashop.export.mapper"
    _inherit = ["base.prestashop.connector", "base.export.mapper"]
    _usage = "export.mapper"

    def _map_direct(self, record, from_attr, to_attr):
        res = super()._map_direct(record, from_attr, to_attr) or ""
        if not isinstance(from_attr, str):
            return res
        column = self.model.fields_get()[from_attr]
        if column["type"] == "boolean":
            return res and 1 or 0
        elif column["type"] == "float":
            set_precision = False
            # We've got column so from_attr is already in self.model._fields
            if isinstance(res, (float, int)):
                # force float precision:
                digits = column["digits"]
                if digits and isinstance(digits[1], int):
                    # Any reason we need more than 12 decimals?
                    fmt = "{:." + str(max(digits[1], 12)) + "f}"
                    res = fmt.format(res)
                    set_precision = True
            if not set_precision:
                res = str(res)
        return res


class TranslationPrestashopExportMapper(AbstractComponent):
    _name = "translation.prestashop.export.mapper"
    _inherit = "prestashop.export.mapper"
    #    _usage = 'translation.export.mapper'

    def changed_by_fields(self):
        """Build a set of fields used by the mapper

        It adds the translatable fields in the set.
        """
        changed_by = super().changed_by_fields()
        if getattr(self, "_translatable_fields", None):
            for from_attr, __ in self._translatable_fields:
                fieldname = self._direct_source_field_name(from_attr)
                changed_by.add(fieldname)
        return changed_by

    @mapping
    def translatable_fields(self, record):
        fields = getattr(self, "_translatable_fields", [])
        if fields:
            translated_fields = self._convert_languages(
                self._get_record_by_lang(record), fields
            )
            return translated_fields
        return {}

    def _get_record_by_lang(self, record):
        # get the backend's languages
        languages = self.backend_record.language_ids
        records = {}
        # for each languages:
        for language in languages:
            # get the translated record
            record = record.with_context(lang=language["code"])
            # put it in the dict
            records[language["prestashop_id"]] = record
        return records

    def _convert_languages(self, records_by_language, translatable_fields):
        res = {}
        for from_attr, to_attr in translatable_fields:
            value = {"language": []}
            for language_id, record in records_by_language.items():
                value["language"].append(
                    {
                        "attrs": {"id": str(language_id)},
                        "value": record[from_attr] or "",
                    }
                )
            res[to_attr] = value

        return res
