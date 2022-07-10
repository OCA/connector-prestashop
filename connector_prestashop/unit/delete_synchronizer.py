# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Deleter
from ..connector import get_environment
from ..backend import prestashop


class PrestashopDeleter(Deleter):
    """ Base deleter for PrestaShop """

    def run(self, resource, external_id):
        """ Run the synchronization, delete the record on PrestaShop

        :param external_id: identifier of the record to delete
        """
        self.backend_adapter.delete(resource, external_id)
        return _('Record %s deleted on PrestaShop on resource %s') % (
            external_id, resource)

PrestashopDeleteSynchronizer = PrestashopDeleter  # Deprecated


@prestashop
class ProductImageDelete(PrestashopDeleter):
    _model_name = 'prestashop.product.image'

    def delete(self, id):
        """ Delete a record on the external system """
        return self._call('%s.delete' % self._prestashop_model, [int(id)])


@prestashop
class ProductCombinationDelete(PrestashopDeleter):
    _model_name = 'prestashop.product.combination'

    def delete(self, id):
        """ Delete a record on the external system """
        return self._call('%s.delete' % self._prestashop_model, [int(id)])


@job(default_channel='root.prestashop')
def export_delete_record(
        session, model_name, backend_id, external_id, resource):
    """ Delete a record on PrestaShop """
    env = get_environment(session, model_name, backend_id)
    deleter = env.get_connector_unit(PrestashopDeleter)
    return deleter.run(resource, external_id)
