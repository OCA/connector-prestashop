# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.addons.component.core import Component


class SpecificPriceDeleter(Component):
    _name = 'prestashop.specific.price.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = 'prestashop.specific.price'

    def _run(self, **kwargs):
        if self.prestashop_id:
            resource = self.backend_adapter._prestashop_model +\
                '/%s' % self.prestashop_id
            res = self.backend_adapter.delete(resource, self.prestashop_id)
            return res
        else:
            return _('Nothing to delete.')
