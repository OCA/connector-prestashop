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


class prestashop_delivery_carrier(orm.Model):
    _name = 'prestashop.delivery.carrier'
    _inherit = 'prestashop.binding'
    _inherits = {'delivery.carrier': 'openerp_id'}
    _description = 'Prestashop Carrier'

    _columns = {
        'openerp_id': fields.many2one(
            'delivery.carrier',
            string='Delivery carrier',
            required=True,
            ondelete='cascade'
        ),
        'id_reference': fields.integer(
            'Id reference',
            help="In Prestashop, carriers with the same 'id_reference' are "
                 "some copies from the first one id_reference (only the last "
                 "one copied is taken account ; and the only one which "
                 "synchronized with erp)"
        ),
        'name_ext': fields.char(
            'External name',
            size=64
        ),
        'active_ext': fields.boolean('External active', help="... in prestashop"),
        'export_tracking': fields.boolean(
            'Export tracking numbers',
            help=" ... in prestashop"
        ),
    }

    _defaults = {
        'export_tracking': False,
    }

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A delivry carrier with the same ID on PrestaShop already exists.'),
    ]


class delivery_carrier(orm.Model):
    _inherit = "delivery.carrier"
    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.delivery.carrier',
            'openerp_id',
            string='PrestaShop Bindings',),
        'company_id': fields.many2one('res.company', 'Company', select=1, required=True),
    }


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
        ('name', 'name'),
        ('id_reference', 'id_reference'),
    ]

    @mapping
    def active(self, record):
        return {'active_ext': record['active'] == '1'}

    @mapping
    def product_id(self, record):
        prod_mod = self.session.pool['product.product']
        default_ship_product = prod_mod.search(
            self.session.cr,
            self.session.uid,
            [('default_code', '=', 'SHIP')],
        )
        if default_ship_product:
            ship_product_id = default_ship_product[0]
        else:
            ship_product_id = prod_mod.search(
                self.session.cr,
                self.session.uid,
                []
            )[0]
        return {'product_id': ship_product_id}

    @mapping
    def partner_id(self, record):
        partner_pool = self.session.pool['res.partner']
        default_partner = partner_pool.search(
            self.session.cr,
            self.session.uid,
            [],
        )[0]
        return {'partner_id': default_partner}

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


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
