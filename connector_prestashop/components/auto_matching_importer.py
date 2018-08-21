# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component

from odoo import _, exceptions

_logger = logging.getLogger(__name__)


class AutoMatchingImporter(Component):
    _name = 'prestashop.auto.matching.importer'
    _inherit = 'prestashop.importer'
    _usage = 'auto.matching.importer'

    _erp_field = None
    _ps_field = None
    _copy_fields = []

    def _compare_function(ps_val, erp_val, ps_dict, erp_dict):
        raise NotImplementedError

    def run(self):
        _logger.debug(
            "[%s] Starting synchro between Odoo and PrestaShop"
            % self.model._name
        )
        nr_ps_already_mapped = 0
        nr_ps_mapped = 0
        nr_ps_not_mapped = 0
        erp_model_name = self.model._inherits.iterkeys().next()
        erp_rec_name = self.env[erp_model_name]._rec_name
        model = self.env[erp_model_name].with_context(active_test=False)
        erp_ids = model.search([])
        erp_list_dict = erp_ids.read()
        adapter = self.component(usage='backend.adapter')
        # Get the IDS from PS
        ps_ids = adapter.search()
        if not ps_ids:
            raise exceptions.Warning(
                _('Failed to query %s via PS webservice')
                % adapter.prestashop_model
            )

        binder = self.binder_for()
        # Loop on all PS IDs
        for ps_id in ps_ids:
            # Check if the PS ID is already mapped to an OE ID
            record = binder.to_internal(ps_id)
            if record:
                # Do nothing for the PS IDs that are already mapped
                _logger.debug(
                    "[%s] PrestaShop ID %s is already mapped to Odoo ID %s"
                    % (self.model._name, ps_id, record.id)
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
                        record = self.model.create(data)
                        binder.bind(ps_id, record)
                        _logger.debug(
                            "[%s] Mapping PrestaShop '%s' (%s) "
                            "to Odoo '%s' (%s) " %
                            (self.model._name,
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
                        "[%s] PrestaShop '%s' (%s) was not mapped "
                        "to any Odoo entry" %
                        (self.model._name,
                         ps_dict['name'],
                         ps_dict[self._ps_field]))

                    nr_ps_not_mapped += 1

        _logger.info(
            "[%s] Synchro between Odoo and PrestaShop successfull"
            % self.model._name
        )
        _logger.info(
            "[%s] Number of PrestaShop entries already mapped = %s"
            % (self.model._name, nr_ps_already_mapped)
        )
        _logger.info(
            "[%s] Number of PrestaShop entries mapped = %s"
            % (self.model._name, nr_ps_mapped)
        )
        _logger.info(
            "[%s] Number of PrestaShop entries not mapped = %s"
            % (self.model._name, nr_ps_not_mapped)
        )

        return True
