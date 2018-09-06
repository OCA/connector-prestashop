# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools.translate import _
from odoo.addons.component.core import AbstractComponent


class PrestashopDeleter(AbstractComponent):
    """ Base deleter for PrestaShop """

    _name = 'prestashop.deleter'
    _inherit = 'base.deleter'
    _usage = 'record.exporter.deleter'

    def run(self, resource, external_id):
        """ Run the synchronization, delete the record on PrestaShop

        :param external_id: identifier of the record to delete
        """
        self.backend_adapter.delete(resource, external_id)
        return _('Record %s deleted on PrestaShop on resource %s') % (
            external_id, resource)
