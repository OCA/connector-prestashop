# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools.translate import _
from odoo.addons.component.core import AbstractComponent

from odoo.tools.translate import _
from odoo.addons.queue_job.job import job
from odoo.addons.connector.unit.synchronizer import Deleter


class PrestashopDeleter(AbstractComponent):
    """ Base deleter for PrestaShop """

    _name = 'prestashop.exporter.deleter'
    _inherit = 'base.deleter'
    _usage = 'record.exporter.deleter'

    def run(self, resource, external_id):
        """ Run the synchronization, delete the record on PrestaShop

        :param external_id: identifier of the record to delete
        """
        self.backend_adapter.delete(resource, external_id)
        return _('Record %s deleted on PrestaShop on resource %s') % (
            external_id, resource)


@job(default_channel='root.prestashop')
def export_delete_record(
        session, model_name, backend_id, external_id, resource):
    """ Delete a record on PrestaShop """
    backend = session.env['prestashop.backend'].browse(backend_id)
    env = backend.get_environment(model_name, session=session)
    deleter = env.get_connector_unit(PrestashopDeleter)
    return deleter.run(resource, external_id)
