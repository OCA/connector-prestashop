# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2013 Akretion (http://www.akretion.com).
#   Copyright (C) 2013 Camptocamp (http://www.camptocamp.com)
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#   @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
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

from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import DeleteSynchronizer
from ..connector import get_environment


class PrestashopDeleteSynchronizer(DeleteSynchronizer):
    """ Base deleter for Prestashop """

    def run(self, external_id):
        """ Run the synchronization, delete the record on Prestashop

        :param external_id: identifier of the record to delete
        """
        self.backend_adapter.delete(external_id)
        return _('Record %s deleted on Prestashop') % external_id


@job
def export_delete_record(session, model_name, backend_id, external_id):
    """ Delete a record on Prestashop """
    env = get_environment(session, model_name, backend_id)
    deleter = env.get_connector_unit(PrestashopDeleteSynchronizer)
    return deleter.run(external_id)
