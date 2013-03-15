# -*- coding: utf-8 -*-
###############################################################################
#
#   connector-ecommerce for OpenERP
#   Copyright (C) 2013-TODAY Akretion <http://www.akretion.com>.
#     @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import logging

from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from ..backend import prestashop

_logger = logging.getLogger(__name__)




class DirectBinder(ConnectorUnit):
    _model_name = None
    _oe_field = None
    _ps_field = None

    def _compare_function(ps_val, oe_val, ps_dict, oe_dict):
        raise NotImplementedError


    def run(self):
        _logger.debug("[%s] Starting synchro between OERP and PS" 
                      %self.model._description)
        nr_ps_already_mapped = 0
        nr_ps_mapped = 0
        nr_ps_not_mapped = 0
        # Get all OERP obj
        sess = self.session
        oe_model_name = self.model._inherits.iterkeys().next()
        oe_rec_name = sess.pool[oe_model_name]._rec_name
        oe_ids = sess.search(oe_model_name, [])
        oe_list_dict = sess.read(oe_model_name, oe_ids, [])
        adapter = self.get_connector_unit_for_model(BackendAdapter)
        # Get the IDS from PS
        ps_ids = adapter.search()
        if not ps_ids:
            raise osv.except_osv(_('Error :'),
                        _('Failed to query %s via PS webservice')
                        %adapter.prestashop_model)

        binder = self.get_binder_for_model()
        # Loop on all PS IDs
        for ps_id in ps_ids:
            # Check if the PS ID is already mapped to an OE ID
            oe_id = binder.to_openerp(ps_id)
            if oe_id:
                # Do nothing for the PS IDs that are already mapped
                _logger.debug("[%s] PS ID %s is already mapped to OERP ID %s"
                        %(self.model._description, ps_id, oe_id))
                nr_ps_already_mapped += 1
            else:
                # PS IDs not mapped => I try to match between the PS ID and the OE ID
                # I read field in PS
                ps_dict = adapter.read(ps_id)
                mapping_found = False
                # Loop on OE IDs
                for oe_dict in oe_list_dict:
                    # Search for a match
                    oe_val = oe_dict[self._oe_field]
                    ps_val = ps_dict[self._ps_field]
                    if self._compare_function(ps_val, oe_val, ps_dict, oe_dict):
                        # it matches, so I write the external ID
                        ps_oe_id = sess.create(self._model_name, {
                                        'openerp_id': oe_dict['id'],
                                        'backend_id': self.backend_record.id
                                        })
                        binder.bind(ps_id, ps_oe_id)
                        _logger.debug(
                            "[%s] Mapping PS '%s' (%s) to OERP '%s' (%s)"
                            % (self.model._description,
                               ps_dict['name'], #not hardcode if needed
                               ps_dict[self._ps_field],
                               oe_dict[oe_rec_name],
                               oe_dict[self._oe_field]))
                        nr_ps_mapped += 1
                        mapping_found = True
                        break
                if not mapping_found:
                    # if it doesn't match, I just print a warning
                    _logger.warning(
                        "[%s] PS '%s' (%s) was not mapped to any OERP entry"
                        % (self.model._description,
                           ps_dict['name'],
                           ps_dict[self._ps_field]))

                    nr_ps_not_mapped += 1

        _logger.info("[%s] Synchro between OERP and PS successfull"
            %self.model._description)
        _logger.info("[%s] Number of PS entries already mapped = %s"
            % (self.model._description, nr_ps_already_mapped))
        _logger.info("[%s] Number of PS entries mapped = %s"
            % (self.model._description, nr_ps_mapped))
        _logger.info("[%s] Number of PS entries not mapped = %s"
            % (self.model._description, nr_ps_not_mapped))

        return True

@prestashop
class LangDirectBinder(DirectBinder):
    _model_name = 'prestashop.res.lang'
    _oe_field = 'code'
    _ps_field = 'language_code'


    def _compare_function(self, ps_val, oe_val, ps_dict, oe_dict):
        if len(oe_val) >= 2 and len(ps_val) >= 2 and \
                    oe_val[0:2].lower() == ps_val[0:2].lower():
            return True
        return False


@prestashop
class CountryDirectBinder(DirectBinder):
    _model_name = 'prestashop.res.country'
    _oe_field = 'code'
    _ps_field = 'iso_code'

    def _compare_function(self, ps_val, oe_val, ps_dict, oe_dict):
        if len(oe_val) >= 2 and len(ps_val) >= 2 and \
                    oe_val[0:2].lower() == ps_val[0:2].lower():
            return True
        return False


@prestashop
class ResCurrencyDirectBinder(DirectBinder):
    _model_name = 'prestashop.res.currency'
    _oe_field = 'name'
    _ps_field = 'iso_code'

    def _compare_function(self, ps_val, oe_val, ps_dict, oe_dict):
        if len(oe_val) == 3 and len(ps_val) == 3 and \
                    oe_val[0:3].lower() == ps_val[0:3].lower():
            return True
        return False

@prestashop
class AccountTaxDirectBinder(DirectBinder):
    _model_name = 'prestashop.account.tax'
    _oe_field = 'amount'
    _ps_field = 'rate'


    def _compare_function(self, ps_val, oe_val, ps_dict, oe_dict):
        if oe_dict['type_tax_use'] == 'sale' and \
                abs(oe_val*100 - float(ps_val))<0.01:
            return True
