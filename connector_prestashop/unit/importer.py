# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.connector import ConnectorUnit
from ..connector import get_environment
from ..connector import add_checkpoint


_logger = logging.getLogger(__name__)


class PrestashopImporter(Importer):
    """ Base importer for PrestaShop """

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(PrestashopImporter, self).__init__(environment)
        self.prestashop_id = None
        self.prestashop_record = None

    def _get_prestashop_data(self):
        """ Return the raw prestashop data for ``self.prestashop_id`` """
        return self.backend_adapter.read(self.prestashop_id)

    def _has_to_skip(self):
        """ Return True if the import can be skipped """
        return False

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        return

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` or
        ``Model.update`` if some fields are missing

        Raise `InvalidDataError`
        """
        return

    def _get_binding(self):
        """Return the openerp id from the prestashop id"""
        return self.binder.to_openerp(self.prestashop_id)

    def _context(self, **kwargs):
        return dict(self.session.context, connector_no_export=True, **kwargs)

    def _create(self, data):
        """ Create the OpenERP record """
        # special check on data before import
        self._validate_data(data)
        binding = self.model.with_context(
            connector_no_export=True
        ).create(data)
        _logger.debug(
            '%d created from prestashop %s', binding, self.prestashop_id)
        return binding

    def _update(self, binding, data):
        """ Update an OpenERP record """
        # special check on data before import
        self._validate_data(data)
        binding.with_context(connector_no_export=True).write(data)
        _logger.debug(
            '%d updated from prestashop %s', binding, self.prestashop_id)
        return

    def _before_import(self):
        """ Hook called before the import, when we have the PrestaShop
        data"""
        return

    def _after_import(self, erp_record):
        """ Hook called at the end of the import """
        return

    def run(self, prestashop_id):
        """ Run the synchronization

        :param prestashop_id: identifier of the record on PrestaShop
        """
        self.prestashop_id = prestashop_id
        self.prestashop_record = self._get_prestashop_data()

        skip = self._has_to_skip()
        if skip:
            return skip

        # import the missing linked resources
        self._import_dependencies()

        map_record = self.mapper.map_record(self.prestashop_record)
        binding = self._get_binding()
        if binding:
            record = map_record.values()
        else:
            record = map_record.values(for_create=True)

        # special check on data before import
        self._validate_data(record)

        if binding:
            self._update(binding, record)
        else:
            binding = self._create(record)

        self.binder.bind(self.prestashop_id, binding)

        self._after_import(binding)

    def _check_dependency(self, external_id, model_name):
        external_id = int(external_id)
        if not self.binder_for(model_name).to_openerp(external_id):
            import_record(
                self.session,
                model_name,
                self.backend_record.id,
                external_id
            )


class BatchImporter(Importer):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """
    page_size = 1000

    def run(self, filters=None, **kwargs):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        if 'limit' in filters:
            self._run_page(filters, **kwargs)
            return
        page_number = 0
        filters['limit'] = '%d,%d' % (
            page_number * self.page_size, self.page_size)
        record_ids = self._run_page(filters, **kwargs)
        while len(record_ids) == self.page_size:
            page_number += 1
            filters['limit'] = '%d,%d' % (
                page_number * self.page_size, self.page_size)
            record_ids = self._run_page(filters, **kwargs)

    def _run_page(self, filters, **kwargs):
        record_ids = self.backend_adapter.search(filters)

        for record_id in record_ids:
            self._import_record(record_id, **kwargs)
        return record_ids

    def _import_record(self, record):
        """ Import a record directly or delay the import of the record """
        raise NotImplementedError


class AddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the underlying model
    (not the prestashop.* but the _inherits'ed model) """

    _model_name = []

    def run(self, binding_id):
        record = self.model.browse(binding_id)
        add_checkpoint(self.session,
                       record._model._name,
                       record.id,
                       self.backend_record.id)


class DirectBatchImporter(BatchImporter):
    """ Import the PrestaShop Shop Groups + Shops

    They are imported directly because this is a rare and fast operation,
    performed from the UI.
    """
    _model_name = None

    def _import_record(self, record):
        """ Import the record directly """
        import_record(
            self.session,
            self.model._name,
            self.backend_record.id,
            record
        )


class DelayedBatchImporter(BatchImporter):
    """ Delay import of the records """
    _model_name = None

    def _import_record(self, record, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(
            self.session,
            self.model._name,
            self.backend_record.id,
            record,
            **kwargs
        )


class TranslatableRecordImporter(PrestashopImporter):
    """ Import one translatable record """
    _model_name = []

    _translatable_fields = {}

    _default_language = 'en_US'

    def _get_oerp_language(self, prestashop_id):
        language_binder = self.binder_for('prestashop.res.lang')
        erp_language = language_binder.to_openerp(prestashop_id)
        return erp_language

    def find_each_language(self, record):
        languages = {}
        for field in self._translatable_fields[self.connector_env.model_name]:
            # TODO FIXME in prestapyt
            if not isinstance(record[field]['language'], list):
                record[field]['language'] = [record[field]['language']]
            for language in record[field]['language']:
                if not language or language['attrs']['id'] in languages:
                    continue
                erp_lang = self._get_oerp_language(language['attrs']['id'])
                if erp_lang:
                    languages[language['attrs']['id']] = erp_lang.code
        return languages

    def _split_per_language(self, record):
        splitted_record = {}
        languages = self.find_each_language(record)
        model_name = self.connector_env.model_name
        for language_id, language_code in languages.items():
            splitted_record[language_code] = record.copy()
            for field in self._translatable_fields[model_name]:
                for language in record[field]['language']:
                    current_id = language['attrs']['id']
                    current_value = language['value']
                    if current_id == language_id:
                        splitted_record[language_code][field] = current_value
                        break
        return splitted_record

    def run(self, prestashop_id):
        """ Run the synchronization

        :param prestashop_id: identifier of the record on PrestaShop
        """
        self.prestashop_id = prestashop_id
        self.prestashop_record = self._get_prestashop_data()
        skip = self._has_to_skip()
        if skip:
            return skip

        # import the missing linked resources
        self._import_dependencies()

        # split prestashop data for every lang
        splitted_record = self._split_per_language(self.prestashop_record)

        binding = None
        if self._default_language in splitted_record:
            binding = self._run_record(
                splitted_record[self._default_language],
                self._default_language
            )
            del splitted_record[self._default_language]

        for lang_code, prestashop_record in splitted_record.items():
            binding = self._run_record(
                prestashop_record,
                lang_code,
                binding=binding
            )

        self.binder.bind(self.prestashop_id, binding)

        self._after_import(binding)

    def _run_record(self, prestashop_record, lang_code, binding=None):
        mapped = self.mapper.map_record(prestashop_record)

        if not binding:
            binding = self._get_binding()

        if binding:
            record = mapped.values()
        else:
            record = mapped.values(for_create=True)

        # special check on data before import
        self._validate_data(record)

        # TODO: Analyze lang in context
        context = self._context()
        context['lang'] = lang_code
        if binding:
            self._update(binding, record)
        else:
            binding = self._create(record)

        return binding


@job(default_channel='root.prestashop')
def import_batch(session, model_name, backend_id, filters=None, **kwargs):
    """ Prepare a batch import of records from PrestaShop """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchImporter)
    importer.run(filters=filters, **kwargs)


@job(default_channel='root.prestashop')
def import_record(session, model_name, backend_id, prestashop_id):
    """ Import a record from PrestaShop """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(PrestashopImporter)
    importer.run(prestashop_id)
