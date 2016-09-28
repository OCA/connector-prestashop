# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import _, exceptions
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.queue.job import related_action
from openerp.addons.connector.unit.synchronizer import Exporter
from .mapper import TranslationPrestashopExportMapper
from ..connector import get_environment


_logger = logging.getLogger(__name__)


# Exporters for PrestaShop.
# In addition to its export job, an exporter has to:
# * check in PrestaShop if the record has been updated more recently than the
#  last sync date and if yes, delay an import
# * call the ``bind`` method of the binder to update the last sync date


class PrestashopBaseExporter(Exporter):
    """ Base exporter for PrestaShop """

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(PrestashopBaseExporter, self).__init__(environment)
        self.binding_id = None
        self.prestashop_id = None

    def _get_openerp_data(self):
        """ Return the raw OpenERP data for ``self.binding_id`` """
        return self.env[self.model._name].browse(self.binding_id)

    def run(self, binding_id, *args, **kwargs):
        """ Run the synchronization

        :param binding_id: identifier of the binding record to export
        """
        self.binding_id = binding_id
        self.erp_record = self._get_openerp_data()

        self.prestashop_id = self.binder.to_backend(self.binding_id)
        result = self._run(*args, **kwargs)

        self.binder.bind(self.prestashop_id, self.binding_id)
        return result

    def _run(self):
        """ Flow of the synchronization, implemented in inherited classes"""
        raise NotImplementedError


class PrestashopExporter(PrestashopBaseExporter):
    """ A common flow for the exports to PrestaShop """

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(PrestashopExporter, self).__init__(environment)
        self.erp_record = None

    def _has_to_skip(self):
        """ Return True if the export can be skipped """
        return False

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        return

    def _map_data(self, fields=None):
        """ Convert the external record to Odoo """
        self.mapper.map_record(self.erp_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` or
        ``Model.update`` if some fields are missing

        Raise `InvalidDataError`
        """
        return

    def _after_export(self):
        """Create records of dependants prestashop objects"""
        return

    def _create(self, data):
        """ Create the PrestaShop record """
        return self.backend_adapter.create(data)

    def _update(self, data):
        """ Update an PrestaShop record """
        assert self.prestashop_id
        return self.backend_adapter.write(self.prestashop_id, data)

    def _run(self, fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.erp_record

        # should be created with all the fields
        if not self.prestashop_id:
            fields = None

        if self._has_to_skip():
            return

        # export the missing linked resources
        self._export_dependencies()
        map_record = self.mapper.map_record(self.erp_record)

        if self.prestashop_id:
            record = map_record.values()
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self._update(record)
        else:
            record = map_record.values(for_create=True)
            if fields is None:
                fields = {}
            record.update(fields)
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self.prestashop_id = self._create(record)
            if self.prestashop_id == 0:
                raise exceptions.Warning(
                    _("Record on PrestaShop have not been created"))
            self._after_export()
        message = _('Record exported with ID %s on PrestaShop.')
        return message % self.prestashop_id


class TranslationPrestashopExporter(PrestashopExporter):

    @property
    def mapper(self):
        if self._mapper is None:
            self._mapper = self.connector_env.get_connector_unit(
                TranslationPrestashopExportMapper)
        return self._mapper

    def _map_data(self, fields=None):
        """ Convert the external record to OpenERP """
        self.mapper.convert(self.get_record_by_lang(), fields=fields)

    def get_record_by_lang(self, record_id):
        # get the backend's languages
        languages = self.backend_record.language_ids
        records = {}
        # for each languages:
        for language in languages:
            # get the translated record
            record = self.model.with_context(
                lang=language['code']).browse(record_id)
            # put it in the dict
            records[language['prestashop_id']] = record
        return records


def related_action_record(session, job):
    binding_model = job.args[0]
    binding_id = job.args[1]
    record = session.env[binding_model].browse(binding_id)
    odoo_name = record.odoo_id._name

    action = {
        'name': _(odoo_name),
        'type': 'ir.actions.act_window',
        'res_model': odoo_name,
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': record.odoo_id.id,
    }
    return action


@job(default_channel='root.prestashop')
@related_action(action=related_action_record)
def export_record(session, model_name, binding_id, fields=None):
    """ Export a record on PrestaShop """
    # TODO: FIX PRESTASHOP do not support partial edit
    fields = None
    record = session.env[model_name].browse(binding_id)
    env = get_environment(session, model_name, record.backend_id.id)
    exporter = env.get_connector_unit(PrestashopExporter)
    return exporter.run(binding_id, fields=fields)
