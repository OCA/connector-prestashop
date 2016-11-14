# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api

from openerp.addons.connector.session import ConnectorSession
from ..custom_info_option.importer import import_product_features


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    import_product_features_since = fields.Datetime(
        string='Import Product Features Since')

    @api.multi
    def import_product_features(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = backend_record.import_product_features_since
            import_product_features.delay(
                session,
                backend_record.id,
                since_date,
                priority=10)
        return True

    @api.model
    def _scheduler_import_product_features(self, domain=None):
        self.search(domain or []).import_product_features()
