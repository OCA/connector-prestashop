# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api

from openerp.addons.connector.session import ConnectorSession
from ..res_partner.importer import import_manufacturers


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    import_manufacturers_since = fields.Datetime('Import Manufacturers since')

    @api.multi
    def import_manufacturers(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            since_date = self._date_as_user_tz(
                backend_record.import_manufacturers_since)
            import_manufacturers.delay(session, backend_record.id, since_date)
        return True

    @api.model
    def _scheduler_import_manufacturers(self, domain=None):
        self.search(domain or []).import_manufacturers()
