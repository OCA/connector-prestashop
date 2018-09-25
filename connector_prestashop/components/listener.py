# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class PrestashopListener(AbstractComponent):
    """ Base Backend Adapter for the connectors """

    _name = 'prestashop.connector.listener'
    _inherit = 'base.connector.listener'

    def need_to_export(self, record, fields=None):
        """ Check if the record has to be exported to prestashop.
        It depends on the written fields and if the record has flag no_export

        To be used with :func:`odoo.addons.component_event.skip_if`
        on Events::

            from odoo.addons.component.core import Component
            from odoo.addons.component_event import skip_if


            class MyEventListener(Component):
                _name = 'my.event.listener'
                _inherit = 'base.connector.event.listener'
                _apply_on = ['magento.res.partner']

                @skip_if(lambda: self, record, *args, **kwargs:
                         self.need_to_export(record, fields=fields))
                def on_record_write(self, record, fields=None):
                    record.with_delay().export_record()

        """
        if not record or not record.backend_id:
            return True
        with record.backend_id.work_on(record._name) as work:
            mapper = work.component(usage='export.mapper')
            exported_fields = mapper.changed_by_fields()
            if fields:
                if not exported_fields & set(fields):
                    _logger.debug(
                        "Skip export of %s because modified fields: %s are "
                        "not part of exported fields %s",
                        record, fields, list(exported_fields))
                    return True
        if record.no_export:
            _logger.debug(
                "Skip export of %s because export is disable for it", record)
            return True
        return False
