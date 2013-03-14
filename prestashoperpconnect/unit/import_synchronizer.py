# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright 2013 Camptocamp SA
#    @author: Guewen Baconnier
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
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
            ]

    def _import_record(self, record):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            record)


