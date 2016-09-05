# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class SyncProducts(models.TransientModel):
    _name = 'active.deactive.products'

    force_status = fields.Boolean(
        string='Force Status',
        help='Check this option to force active product in prestashop')

    def _change_status(self, status):
        self.ensure_one()
        product_obj = self.env['product.template']
        for product in product_obj.browse(self.env.context['active_ids']):
            for bind in product.prestashop_bind_ids:
                if bind.always_available != status or self.force_status:
                    bind.always_available = status

    @api.multi
    def active_products(self):
        self._change_status(True)

    @api.multi
    def deactive_products(self):
        self._change_status(False)
