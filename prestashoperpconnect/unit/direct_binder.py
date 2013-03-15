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

_logger = logging.getLogger(__name__)



class DirectBinder(ConnectorUnit):
    _model_name = None
    _oe_field = None
    _ps_model = None
    _ps_field = None


    def run():
        _logger.debug("[%s] Starting synchro between OERP and PS") 
                      %self.model.name)
        #K referential_id = external_session.referential_id.id
        nr_ps_already_mapped = 0
        nr_ps_mapped = 0
        nr_ps_not_mapped = 0
        # Get all OERP obj
        oe_ids = self.session.search([])
        fields_to_read = list(set(self._rec_name, self._oe_field))
        oe_list_dict = self.model.read(cr, uid, oe_ids, fields_to_read,
                                       context=context)
        adapter = self.get_connector_unit_for_model(BackendAdapter)
        # Get the IDS from PS
        ps_ids = adapter.search()
        #print "ps_ids=", ps_ids
        if not ps_ids:
            raise osv.except_osv(_('Error :'),
                        _('Failed to query %s via PS webservice')% self._ps_model)

        binder = self.get_binder_for_model()
        # Loop on all PS IDs
        for ps_id in ps_ids:
            # Check if the PS ID is already mapped to an OE ID
            oe_id = binder.to_openerp_id(ps_id)
            #print "oe_c_id=", oe_id
            if oe_id:
                # Do nothing for the PS IDs that are already mapped
                _logger.debug("[%s] PS ID %s is already mapped to OERP ID %s"
                        %(self.model.name, ps_id, oe_id))
                nr_ps_already_mapped += 1
            else:
                # PS IDs not mapped => I try to match between the PS ID and the OE ID
                # I read field in PS
                ps_dict = adapter.read(ps_id)
                #print "ps_dict=", ps_dict
                mapping_found = False
                # Loop on OE IDs
                for oe_dict in oe_list_dict:
                    # Search for a match
                    if self._compare_function(ps_dict, oe_dict):
                        # it matches, so I write the external ID
                        binder.bind(ps_id, oe_id)
                        _logger.debug(
                            _("[%s] Mapping PS '%s' (%s) to OERP '%s' (%s)")
                            % (self.model.name,
                               ps_dict[0]['name'], #not hardcode if needed
                               ps_dict[0][self._ps_field],
                               oe_dict[self._rec_name],
                               oe_dict[self._oe_field]))
                        nr_ps_mapped += 1
                        mapping_found = True
                        break
                if not mapping_found:
                    # if it doesn't match, I just print a warning
                    external_session.logger.warning(
                        _("[%s] PS '%s' (%s) was not mapped to any OERP entry")
                        % (self.model.name,
                           ps_dict[0]['name'],
                           ps_dict[0][self._ps_field]))

                    nr_ps_not_mapped += 1

        _logger.debug("[%s] Synchro between OERP and PS successfull"
            %self.model.name)
        _logger.debug("[%s] Number of PS entries already mapped = %s"
            % (self.model.name, nr_ps_already_mapped))
        _logger.debug("[%s] Number of PS entries mapped = %s"
            % (self.model.name, nr_ps_mapped))
        _logger.debug("[%s] Number of PS entries not mapped = %s"
            % (self.model.name, nr_ps_not_mapped)

       return True

class LangDirectBinder(DirectBinder):
    _model_name = 'res.lang'
    _oe_field = 'code'
    _ps_model = 'countries'
    _ps_field = 'language_code'


    def _compare_function(ps_dict, oe_dict):
        oe_val = oe_dict[self._oe_field]
        ps_val = ps_dict[0][self._ps_field]
        if len(oe_val) >= 2 and len(ps_val) >= 2 and \
                    oe_val[0:2].lower() == ps_val[0:2].lower():
            return True
        else:
            return False

