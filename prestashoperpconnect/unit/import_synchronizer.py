# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright 2013 Camptocamp SA
#    @author: Guewen Baconnier
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import ImportSynchronizer
from ..backend import prestashop
from ..connector import get_environment

_logger = logging.getLogger(__name__)


class PrestashopImportSynchronizer(ImportSynchronizer):
    """ Base importer for Prestashop """

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.Environment`
        """
        super(PrestashopImportSynchronizer, self).__init__(environment)
        self.prestashop_id = None
        self.prestashop_record = None

    def _get_prestashop_data(self):
        """ Return the raw Magento data for ``self.prestashop_id`` """
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

    def _get_openerp_id(self):
        """Return the openerp id from the prestashop id"""
        return self.binder.to_openerp(self.prestashop_id)

    def _context(self, **kwargs):
        return dict(self.session.context, connector_no_export=True, **kwargs)

    def _create(self, data, context=None):
        """ Create the OpenERP record """
        if context is None:
            context = self._context()
        openerp_id = self.model.create(self.session.cr,
                                       self.session.uid,
                                       data,
                                       context=context)
        _logger.debug('%s %d created from prestashop %s',
                      self.model._name, openerp_id, self.prestashop_id)
        return openerp_id

    def _update(self, openerp_id, data, context=None):
        """ Update an OpenERP record """
        if context is None:
            context = self._context()
        self.model.write(self.session.cr,
                         self.session.uid,
                         openerp_id,
                         data,
                         context=context)
        _logger.debug('%s %d updated from prestashop %s',
                      self.model._name, openerp_id, self.prestashop_id)
        return

    def _after_import(self, openerp_id):
        """ Hook called at the end of the import """
        return

    def run(self, prestashop_id):
        """ Run the synchronization

        :param prestashop_id: identifier of the record on Prestashop
        """
        self.prestashop_id = prestashop_id
        self.prestashop_record = self._get_prestashop_data()

        skip = self._has_to_skip()
        if skip:
            return skip

        # import the missing linked resources
        self._import_dependencies()

        openerp_id = self._get_openerp_id()
        self.mapper.convert(self.prestashop_record)
        if openerp_id:
            record = self.mapper.data
        else:
            record = self.mapper.data_for_create

        # special check on data before import
        self._validate_data(record)

        if openerp_id:
            self._update(openerp_id, record)
        else:
            openerp_id = self._create(record)

        self.binder.bind(self.prestashop_id, openerp_id)

        self._after_import(openerp_id)


class BatchImportSynchronizer(ImportSynchronizer):
    """ The role of a BatchImportSynchronizer is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    def run(self, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters)
        for record_id in record_ids:
            self._import_record(record_id)

    def _import_record(self, record):
        """ Import a record directly or delay the import of the record """
        raise NotImplementedError


@prestashop
class DirectBatchImport(BatchImportSynchronizer):
    """ Import the PrestaShop Shop Groups + Shops

    They are imported directly because this is a rare and fast operation,
    performed from the UI.
    """
    _model_name = [
        'prestashop.shop.group',
        'prestashop.shop',
        'prestashop.product.category',
    ]

    def _import_record(self, record):
        """ Import the record directly """
        import_record(
            self.session,
            self.model._name,
            self.backend_record.id,
            record
        )


@prestashop
class DelayedBatchImport(BatchImportSynchronizer):
    """ Delay import of the records """
    _model_name = [
        'prestashop.res.partner.category',
        'prestashop.res.partner',
        'prestashop.address',
        'prestashop.product',
    ]

    def _import_record(self, record):
        """ Delay the import of the records"""
        import_record.delay(
            self.session,
            self.model._name,
            self.backend_record.id,
            record
        )


@prestashop
class SimpleRecordImport(PrestashopImportSynchronizer):
    """ Import one simple record """
    _model_name = [
        'prestashop.shop.group',
        'prestashop.shop',
        'prestashop.res.partner',
        'prestashop.address',
    ]


@prestashop
class TranslatableRecordImport(PrestashopImportSynchronizer):
    """ Import one translatable record """
    _model_name = [
        'prestashop.res.partner.category',
        'prestashop.product.category',
        'prestashop.product',
    ]

    _translatable_fields = {
        'prestashop.res.partner.category': ['name'],
        'prestashop.product.category': [
            'name',
            'description',
            'link_rewrite',
            'meta_description',
            'meta_keywords',
            'meta_title'
        ],
        'prestashop.product': [
            'name',
            'description',
        ],
    }

    _default_language = 'en_US'

    def _get_oerp_language(self, prestashop_id):
        language_binder = self.get_binder_for_model('prestashop.res.lang')
        oerp_language_id = language_binder.to_openerp(prestashop_id)
        model = self.environment.session.pool.get('prestashop.res.lang')
        oerp_lang = model.read(
            self.session.cr,
            self.session.uid,
            oerp_language_id,
        )
        return oerp_lang

    def find_each_language(self, record):
        languages = {}
        for field in self._translatable_fields[self.environment.model_name]:
            for language in record[field]['language']:
                if language['attrs']['id'] in languages:
                    continue
                oerp_lang = self._get_oerp_language(language['attrs']['id'])
                languages[language['attrs']['id']] = oerp_lang['code']
        return languages

    def _split_per_language(self, record):
        splitted_record = {}
        languages = self.find_each_language(record)
        model_name = self.environment.model_name
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

        :param prestashop_id: identifier of the record on Prestashop
        """
        self.prestashop_id = prestashop_id
        prestashop_record = self._get_prestashop_data()

        skip = self._has_to_skip()
        if skip:
            return skip

        # import the missing linked resources
        self._import_dependencies()

        #split prestashop data for every lang
        splitted_record = self._split_per_language(prestashop_record)

        openerp_id = None

        if self._default_language in splitted_record:
            openerp_id = self._run_record(
                splitted_record[self._default_language],
                self._default_language
            )
            del splitted_record[self._default_language]

        for lang_code, prestashop_record in splitted_record.items():
            openerp_id = self._run_record(
                prestashop_record,
                lang_code,
                openerp_id
            )

        self.binder.bind(self.prestashop_id, openerp_id)

        self._after_import(openerp_id)

    def _run_record(self, prestashop_record, lang_code, openerp_id=None):
        self.mapper.convert(prestashop_record)

        if openerp_id is None:
            openerp_id = self._get_openerp_id()

        if openerp_id:
            record = self.mapper.data
        else:
            record = self.mapper.data_for_create

        # special check on data before import
        self._validate_data(record)

        context = self._context()
        context['lang'] = lang_code
        if openerp_id:
            self._update(openerp_id, record, context)
        else:
            openerp_id = self._create(record, context)

        return openerp_id


@job
def import_batch(session, model_name, backend_id, filters=None):
    """ Prepare a batch import of records from Prestashop """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchImportSynchronizer)
    importer.run(filters=filters)


@job
def import_record(session, model_name, backend_id, prestashop_id):
    """ Import a record from Prestashop """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(PrestashopImportSynchronizer)
    importer.run(prestashop_id)


@job
def import_partners_since(session, model_name, backend_id, since_date=None):
    """ Prepare the import of partners modified on Prestashop """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchImportSynchronizer)
    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    # TODO : do something with since_date, but prestashop does not allow to
    # filter on date_upd field...
    importer.run()

    session.pool.get('prestashop.backend').write(
        session.cr,
        session.uid,
        backend_id,
        {'import_partners_since': now_fmt},
        context=session.context
    )
