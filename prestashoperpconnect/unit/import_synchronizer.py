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
from openerp.addons.connector.connector import Environment
from openerp.addons.connector.unit.synchronizer import ImportSynchronizer
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
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

    def _map_data(self):
        """ Return the external record converted to OpenERP """
        return self.mapper.convert(self.prestashop_record)

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

    def _create(self, data):
        """ Create the OpenERP record """
        openerp_id = self.model.create(self.session.cr,
                                       self.session.uid,
                                       data,
                                       context=self._context())
        _logger.debug('%s %d created from prestashop %s',
                      self.model._name, openerp_id, self.prestashop_id)
        return openerp_id

    def _update(self, openerp_id, data):
        """ Update an OpenERP record """
        self.model.write(self.session.cr,
                         self.session.uid,
                         openerp_id,
                         data,
                         context=self._context())
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

        record = self._map_data()

        # special check on data before import
        self._validate_data(record)

        openerp_id = self._get_openerp_id()

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
            ]

    def _import_record(self, record):
        """ Import the record directly """
        import_record(self.session,
                      self.model._name,
                      self.backend_record.id,
                      record)


@prestashop
class DelayedBatchImport(BatchImportSynchronizer):
    """ Delay import of the records """
    _model_name = [
            'res.currency',
            'res.country',
            'res.lang',
            'prestashop.res.partner.category'
            ]

    def _import_record(self, record):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            record)

@prestashop
class SimpleRecordImport(PrestashopImportSynchronizer):
    """ Import one simple record """
    _model_name = [
            'prestashop.shop.group',
            'prestashop.shop',
        ]

@prestashop
class TranslatableRecordImport(PrestashopImportSynchronizer):
    """ Import one translatable record """
    _model_name = [
            'prestashop.res.partner.category'
        ]

    def _split_per_language(self):
        import pdb; pdb.set_trace()
        return splited_record

    def _map_data(self, record_to_map):
        return self.mapper.convert(record_to_map)

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

        #split prestashop data for every lang
        splited_record = self._split_per_language()

        default_lang_record = splited_record[0]

        record = self._map_data(default_lang_record)

        # special check on data before import
        self._validate_data(record)

        openerp_id = self._get_openerp_id()

        if openerp_id:
            self._update(openerp_id, record)
        else:
            openerp_id = self._create(record)

        self.binder.bind(self.prestashop_id, openerp_id)

        self._after_import(openerp_id)

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
    # FIXME: this may run a long time after the user has clicked the
    # import button -> the use of datetime.now() should be done in the
    # method called by the button, and not in the async. processing
    # see what is done by the import_sale_orders
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchImportSynchronizer)
    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    filters = {}
    if since_date:
        since_fmt = since_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # updated_at include the created records
        filters['updated_at'] = {'from': since_fmt}
    importer.run(filters=filters)
    session.pool.get('prestashop.backend').write(
            session.cr,
            session.uid,
            backend_id,
            {'import_partners_since': now_fmt},
            context=session.context)
