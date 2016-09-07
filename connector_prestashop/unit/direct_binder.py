# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from ..backend import prestashop

from openerp import _, exceptions

_logger = logging.getLogger(__name__)


class DirectBinder(ConnectorUnit):
    _model_name = None
    _erp_field = None
    _ps_field = None
    _copy_fields = []

    def _compare_function(ps_val, erp_val, ps_dict, erp_dict):
        raise NotImplementedError

    def run(self):
        _logger.debug(
            "[%s] Starting synchro between OERP and PS"
            % self.model._description
        )
        nr_ps_already_mapped = 0
        nr_ps_mapped = 0
        nr_ps_not_mapped = 0
        # Get all OERP obj
        sess = self.session
        erp_model_name = self.model._inherits.iterkeys().next()
        erp_rec_name = sess.env[erp_model_name]._rec_name
        erp_ids = sess.env[erp_model_name].search([])
        erp_list_dict = erp_ids.read()
        adapter = self.unit_for(BackendAdapter)
        # Get the IDS from PS
        ps_ids = adapter.search()
        if not ps_ids:
            raise exceptions.Warning(
                _('Error :'),
                _('Failed to query %s via PS webservice')
                % adapter.prestashop_model
            )

        binder = self.binder_for()
        # Loop on all PS IDs
        for ps_id in ps_ids:
            # Check if the PS ID is already mapped to an OE ID
            erp_id = binder.to_odoo(ps_id).id
            if erp_id:
                # Do nothing for the PS IDs that are already mapped
                _logger.debug(
                    "[%s] PS ID %s is already mapped to OERP ID %s"
                    % (self.model._description, ps_id, erp_id)
                )
                nr_ps_already_mapped += 1
            else:
                # PS IDs not mapped => I try to match between the PS ID and
                # the OE ID. First, I read field in PS
                ps_dict = adapter.read(ps_id)
                mapping_found = False
                # Loop on OE IDs
                for erp_dict in erp_list_dict:
                    # Search for a match
                    erp_val = erp_dict[self._erp_field]
                    ps_val = ps_dict[self._ps_field]
                    if self._compare_function(
                            ps_val, erp_val, ps_dict, erp_dict):
                        # it matches, so I write the external ID
                        data = {
                            'odoo_id': erp_dict['id'],
                            'backend_id': self.backend_record.id,
                        }
                        for oe_field, ps_field in self._copy_fields:
                            data[oe_field] = erp_dict[ps_field]
                        # ps_erp_id = sess.create(self._model_name, data)
                        ps_erp_id = sess.env[self._model_name].create(data)
                        binder.bind(ps_id, ps_erp_id)
                        _logger.debug(
                            "[%s] Mapping PS '%s' (%s) to OERP '%s' (%s)"
                            % (self.model._description,
                               ps_dict['name'],  # not hardcode if needed
                               ps_dict[self._ps_field],
                               erp_dict[erp_rec_name],
                               erp_dict[self._erp_field]))
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

        _logger.info(
            "[%s] Synchro between OERP and PS successfull"
            % self.model._description
        )
        _logger.info(
            "[%s] Number of PS entries already mapped = %s"
            % (self.model._description, nr_ps_already_mapped)
        )
        _logger.info(
            "[%s] Number of PS entries mapped = %s"
            % (self.model._description, nr_ps_mapped)
        )
        _logger.info(
            "[%s] Number of PS entries not mapped = %s"
            % (self.model._description, nr_ps_not_mapped)
        )

        return True


@prestashop
class CarrierDirectBinder(DirectBinder):
    _model_name = 'prestashop.delivery.carrier'
    _erp_field = 'name'
    _ps_field = 'name_ext'
