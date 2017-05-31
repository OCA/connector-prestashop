# -*- coding: utf-8 -*-
# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models
from openerp.addons.connector.session import ConnectorSession
from ..product_specific_price.exporter import export_specific_prices_to_backend


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    @api.multi
    def export_specific_prices(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            export_specific_prices_to_backend.delay(
                session,
                backend_record.id,
                priority=15
            )
        return True
