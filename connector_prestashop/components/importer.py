# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import closing, contextmanager

import odoo
from odoo import _, fields

from odoo.addons.queue_job.job import job
from odoo.addons.queue_job.exception import (
    RetryableJobError,
    FailedJobError,
)

from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.exception import NothingToDoJob

_logger = logging.getLogger(__name__)

RETRY_ON_ADVISORY_LOCK = 1  # seconds
RETRY_WHEN_CONCURRENT_DETECTED = 1  # seconds

def import_record():
    pass
def import_batch():
    pass

class PrestashopBaseImporter(AbstractComponent):
    _name = 'prestashop.base.importer'
    _inherit = ['base.importer', 'base.prestashop.connector']

    def _import_dependency(self, prestashop_id, binding_model,
                           importer_class=None, always=False,
                           **kwargs):
        """
        Import a dependency. The importer class is a subclass of
        ``PrestashopImporter``. A specific class can be defined.

        :param prestashop_id: id of the prestashop id to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_cls: :py:class:`openerp.addons.connector.\
                                        connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: PrestashopImporter
        :type importer_cls: :py:class:`openerp.addons.connector.\
                                       connector.MetaConnectorUnit`
        :param always: if True, the record is updated even if it already
                       exists,
                       it is still skipped if it has not been modified on
                       PrestaShop
        :type always: boolean
        :param kwargs: additional keyword arguments are passed to the importer
        """
        if not prestashop_id:
            return
        if importer_class is None:
            importer_class = PrestashopImporter
        binder = self.binder_for(binding_model)
        if always or not binder.to_internal(prestashop_id):
            importer = self.component(usage='record.importer', model_name=binding_model)
            importer.run(prestashop_id, **kwargs)


class PrestashopImporter(AbstractComponent):
    """ Base importer for PrestaShop """

    _name = 'prestashop.importer'
    _inherit = 'prestashop.base.importer'
    _usage = 'record.importer'

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

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.prestashop_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` or
        ``Model.update`` if some fields are missing

        Raise `InvalidDataError`
        """
        return

    def _get_binding(self):
        """Return the openerp id from the prestashop id"""
        return self.binder.to_internal(self.prestashop_id)

    def _context(self, **kwargs):
        return dict(self._context, connector_no_export=True, **kwargs)

    def _create_context(self):
        return {'connector_no_export': True}

    def _create_data(self, map_record):
        return map_record.values(for_create=True)

    def _update_data(self, map_record):
        return map_record.values()

    def _create(self, data):
        """ Create the OpenERP record """
        # special check on data before import
        self._validate_data(data)
        binding = self.model.with_context(
            **self._create_context()
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

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    @contextmanager
    def do_in_new_connector_env(self, model_name=None):
        """ Context manager that yields a new connector environment

        Using a new Odoo Environment thus a new PG transaction.

        This can be used to make a preemptive check in a new transaction,
        for instance to see if another transaction already made the work.
        """
        with odoo.api.Environment.manage():
            registry = odoo.modules.registry.RegistryManager.get(
                self.env.cr.dbname
            )
            with closing(registry.cursor()) as cr:
                try:
                    new_env = odoo.api.Environment(cr, self.env.uid,
                                                      self.env.context)
                    # connector_env = self.connector_env.create_environment(
                    #     self.backend_record.with_env(new_env),
                    #     model_name or self.model._name,
                    #     connector_env=self.connector_env
                    # )
                    with self.backend_record.with_env(
                        new_env).work_on(self.model._name) as work2:
                        yield work2
                except:
                    cr.rollback()
                    raise
                else:
                    # Despite what pylint says, this a perfectly valid
                    # commit (in a new cursor). Disable the warning.
                    cr.commit()  # pylint: disable=invalid-commit

    def _check_in_new_connector_env(self):
        with self.do_in_new_connector_env() as new_connector_env:
            # Even when we use an advisory lock, we may have
            # concurrent issues.
            # Explanation:
            # We import Partner A and B, both of them import a
            # partner category X.
            #
            # The squares represent the duration of the advisory
            # lock, the transactions starts and ends on the
            # beginnings and endings of the 'Import Partner'
            # blocks.
            # T1 and T2 are the transactions.
            #
            # ---Time--->
            # > T1 /------------------------\
            # > T1 | Import Partner A       |
            # > T1 \------------------------/
            # > T1        /-----------------\
            # > T1        | Imp. Category X |
            # > T1        \-----------------/
            #                     > T2 /------------------------\
            #                     > T2 | Import Partner B       |
            #                     > T2 \------------------------/
            #                     > T2        /-----------------\
            #                     > T2        | Imp. Category X |
            #                     > T2        \-----------------/
            #
            # As you can see, the locks for Category X do not
            # overlap, and the transaction T2 starts before the
            # commit of T1. So no lock prevents T2 to import the
            # category X and T2 does not see that T1 already
            # imported it.
            #
            # The workaround is to open a new DB transaction at the
            # beginning of each import (e.g. at the beginning of
            # "Imp. Category X") and to check if the record has been
            # imported meanwhile. If it has been imported, we raise
            # a Retryable error so T2 is rollbacked and retried
            # later (and the new T3 will be aware of the category X
            # from the its inception).
            binder = self.binder_for(model=self.model._name)
            # binder = new_connector_env.get_connector_unit(Binder)
            if binder.to_internal(self.prestashop_id):
                raise RetryableJobError(
                    'Concurrent error. The job will be retried later',
                    seconds=RETRY_WHEN_CONCURRENT_DETECTED,
                    ignore_retry=True
                )

    def run(self, prestashop_id, **kwargs):
        """ Run the synchronization

        :param prestashop_id: identifier of the record on PrestaShop
        """
        self.prestashop_id = prestashop_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            self.prestashop_id,
        )
        # Keep a lock on this import until the transaction is committed
        self.advisory_lock_or_retry(lock_name,
                                    retry_seconds=RETRY_ON_ADVISORY_LOCK)
        if not self.prestashop_record:
            self.prestashop_record = self._get_prestashop_data()

        binding = self._get_binding()
        if not binding:
            self._check_in_new_connector_env()

        skip = self._has_to_skip()
        if skip:
            return skip

        # import the missing linked resources
        self._import_dependencies()

        self._import(binding, **kwargs)

    def _import(self, binding, **kwargs):
        """ Import the external record.

        Can be inherited to modify for instance the session
        (change current user, values in context, ...)

        """

        map_record = self._map_data()

        if binding:
            record = self._update_data(map_record)
        else:
            record = self._create_data(map_record)

        # special check on data before import
        self._validate_data(record)

        if binding:
            self._update(binding, record)
        else:
            binding = self._create(record)

        self.binder.bind(self.prestashop_id, binding)

        self._after_import(binding)


class BatchImporter(AbstractComponent):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """
    _name = 'prestashop.batch.importer'
    _inherit = ['base.importer', 'base.prestashop.connector']
    _usage = 'batch.importer'

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


class DirectBatchImporter(AbstractComponent):
    """ Import the PrestaShop Shop Groups + Shops

    They are imported directly because this is a rare and fast operation,
    performed from the UI.
    """
    _name = 'prestashop.direct.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _model_name = None

    def _import_record(self, external_id):
        """ Import the record directly """
        self.env[self.model._name].import_record(
            backend=self.backend_record,
            prestashop_id=external_id)


class DelayedBatchImporter(AbstractComponent):
    """ Delay import of the records """

    _name = 'prestashop.delayed.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _model_name = None

    def _import_record(self, external_id, **kwargs):
        """ Delay the import of the records"""
        self.env[self.model._name].with_delay().import_record(
            backend=self.backend_record,
            prestashop_id=external_id,
            **kwargs)


class TranslatableRecordImporter(AbstractComponent):
    """ Import one translatable record """
    _name = 'prestashop.translatable.record.importer'
    _inherit = 'prestashop.importer'

    _model_name = []

    _translatable_fields = {}
    # TODO set default language on the backend
    _default_language = 'en_US'

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(TranslatableRecordImporter, self).__init__(environment)
        self.main_lang_data = None
        self.main_lang = None
        self.other_langs_data = None

    def _get_odoo_language(self, prestashop_id):
        language_binder = self.binder_for('prestashop.res.lang')
        erp_language = language_binder.to_internal(prestashop_id)
        return erp_language

    def find_each_language(self, record):
        languages = {}
        for field in self._translatable_fields[self.model._name]:
            # TODO FIXME in prestapyt
            if not isinstance(record[field]['language'], list):
                record[field]['language'] = [record[field]['language']]
            for language in record[field]['language']:
                if not language or language['attrs']['id'] in languages:
                    continue
                erp_lang = self._get_odoo_language(language['attrs']['id'])
                if erp_lang:
                    languages[language['attrs']['id']] = erp_lang.code
        return languages

    def _split_per_language(self, record, fields=None):
        """Split record values by language.

        @param record: a record from PS
        @param fields: fields whitelist
        @return a dictionary with the following structure:

            'en_US': {
                'field1': value_en,
                'field2': value_en,
            },
            'it_IT': {
                'field1': value_it,
                'field2': value_it,
            }
        """
        split_record = {}
        languages = self.find_each_language(record)
        if not languages:
            raise FailedJobError(
                _('No language mapping defined. '
                  'Run "Synchronize base data".')
            )
        model_name = self.model._name
        for language_id, language_code in languages.iteritems():
            split_record[language_code] = record.copy()
        _fields = self._translatable_fields[model_name]
        if fields:
            _fields = [x for x in _fields if x in fields]
        for field in _fields:
            for language in record[field]['language']:
                current_id = language['attrs']['id']
                code = languages.get(current_id)
                if not code:
                    # TODO: be nicer here.
                    # Currently if you have a language in PS
                    # that is not present in odoo
                    # the basic metadata sync is broken.
                    # We should present skip the language
                    # and maybe show a message to users.
                    raise FailedJobError(
                        _('No language could be found for the Prestashop lang '
                          'with id "%s". Run "Synchronize base data" again.') %
                        (current_id,)
                    )
                split_record[code][field] = language['value']
        return split_record

    def _create_context(self):
        context = super(TranslatableRecordImporter, self)._create_context()
        if self.main_lang:
            context['lang'] = self.main_lang
        return context

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.main_lang_data)

    def _import(self, binding, **kwargs):
        """ Import the external record.

        Can be inherited to modify for instance the session
        (change current user, values in context, ...)

        """
        # split prestashop data for every lang
        split_record = self._split_per_language(self.prestashop_record)
        if self._default_language in split_record:
            self.main_lang_data = split_record[self._default_language]
            self.main_lang = self._default_language
            del split_record[self._default_language]
        else:
            self.main_lang, self.main_lang_data = split_record.popitem()

        self.other_langs_data = split_record

        super(TranslatableRecordImporter, self)._import(binding)

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        for lang_code, lang_record in self.other_langs_data.iteritems():
            map_record = self.mapper.map_record(lang_record)
            binding.with_context(
                lang=lang_code,
                connector_no_export=True,
            ).write(map_record.values())
