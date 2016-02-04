# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: Guewen Baconnier, Sébastien Beau, David Béal
#    Copyright (C) 2010 BEAU Sébastien
#    Copyright 2011-2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp.osv import fields, orm
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper,
                                                  )
from .unit.backend_adapter import GenericAdapter
from .unit.mapper import PrestashopImportMapper
from .unit.import_synchronizer import (DelayedBatchImport,
                                       PrestashopImportSynchronizer,
                                       )
from .backend import prestashop

_logger = logging.getLogger(__name__)


@prestashop
class DeliveryCarrierAdapter(GenericAdapter):
    _model_name = 'prestashop.delivery.carrier'
    _prestashop_model = 'carriers'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        filters['filter[deleted]'] = 0

        return super(DeliveryCarrierAdapter, self).search(filters)


@prestashop
class DeliveryCarrierImport(PrestashopImportSynchronizer):
    _model_name = ['prestashop.delivery.carrier']


@prestashop
class CarrierImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.delivery.carrier'
    direct = [
        ('name', 'name_ext'),
        ('id_reference', 'id_reference'),
    ]

    @mapping
    def active(self, record):
        return {'active_ext': record['active'] == '1'}

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def openerp_id(self, record):
        res = {}
        prestashop_carrier_obj = self.session.pool['prestashop.delivery.carrier']
        existing_carrier_ids = prestashop_carrier_obj.search(
            self.session.cr,
            self.session.uid,
            [('id_reference', '=', record['id_reference']),
             ('backend_id', '=', self.backend_record.id)],
        )
        same_presta_ids_carrier = prestashop_carrier_obj.search(
            self.session.cr,
            self.session.uid,
            [('id_reference', '=', record['id_reference']),
             ('backend_id', '=', self.backend_record.id),
             ('prestashop_id', '=', int(record['id']))],
        )
        #case it is an update
        if same_presta_ids_carrier:
            existing_carrier = prestashop_carrier_obj.browse(
                self.session.cr,
                self.session.uid,
                same_presta_ids_carrier)[0]
            res['openerp_id'] = existing_carrier.openerp_id.id
        #case new carrier in prestashop but exists in OE
        elif existing_carrier_ids:
            existing_carrier = prestashop_carrier_obj.browse(
                self.session.cr,
                self.session.uid,
                existing_carrier_ids)[-1]
            if existing_carrier.openerp_id:
                res['openerp_id'] = existing_carrier.openerp_id.id
            else:
                res['openerp_id'] = False
            prestashop_carrier_obj.unlink(
                self.session.cr,
                self.session.uid,
                existing_carrier_ids)
        else:
            res['openerp_id'] = False
        return res


@prestashop
class DeliveryCarrierBatchImport(DelayedBatchImport):
    """ Import the Prestashop Carriers.
    """
    _model_name = ['prestashop.delivery.carrier']

    def run(self, filters=None, **kwargs):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search()
        _logger.info('search for prestashop carriers %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id, **kwargs)
