# Copyright 2018 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import _


class ProductImageDeleter(Component):
    _name = 'prestashop.product.image.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = 'prestashop.product.image'

    def _run(self, **kwargs):
        if self.prestashop_id:
            record = kwargs.get('record', None)
            res = self.backend_adapter.delete(self.prestashop_id, record)
            return res
        else:
            return _('Nothing to delete.')
