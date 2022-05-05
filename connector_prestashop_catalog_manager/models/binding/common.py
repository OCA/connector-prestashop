# Copyright 2021 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PrestashopBinding(models.AbstractModel):
    _inherit = "prestashop.binding"

    @api.model
    def create(self, vals):
        ctx = self.env.context.copy()
        ctx["catalog_manager_ignore_translation"] = True
        res = super(PrestashopBinding, self.with_context(ctx)).create(vals)

        return res
