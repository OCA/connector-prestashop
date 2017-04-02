# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class PrestashopExportFeature(models.TransientModel):
    _name = 'wiz.prestashop.export.feature'

    def _default_backend(self):
        return self.env['prestashop.backend'].search([], limit=1).id

    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        default=_default_backend,
        string='Backend',
    )

    @api.multi
    def export_features(self):
        self.ensure_one()
        feature_obj = self.env['custom.info.property']
        ps_feature_obj = self.env['prestashop.product.features']
        for feature in feature_obj.browse(self.env.context['active_ids']):
            ps_feature = ps_feature_obj.search([
                ('odoo_id', '=', feature.id),
                ('backend_id', '=', self.backend_id.id),
            ])
            if not ps_feature:
                ps_feature_obj.create({
                    'backend_id': self.backend_id.id,
                    'odoo_id': feature.id,
                })
