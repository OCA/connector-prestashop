# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import _


class ProductCombinationDeleter(Component):
    _name = 'prestashop.product.combination.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = 'prestashop.product.combination'

    def _run(self, **kwargs):
        if self.prestashop_id:
            resource = self.backend_adapter._prestashop_model +\
                '/%s' % self.prestashop_id
            res = self.backend_adapter.delete(resource, self.prestashop_id)
            return res
        else:
            return _('Nothing to delete.')


class ProductCombinationOptionDeleter(Component):
    _name = 'prestashop.product.combination.option.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = [
        'prestashop.product.combination.option',
        'prestashop.product.combination.option.value',
    ]

    def _run(self, **kwargs):
        if self.prestashop_id:
            resource = self.backend_adapter._prestashop_model +\
                '/%s' % self.prestashop_id
            res = self.backend_adapter.delete(resource, self.prestashop_id)
            return res
        else:
            return _('Nothing to delete.')