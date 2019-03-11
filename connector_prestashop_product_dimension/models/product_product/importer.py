# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class DimensionsProductCombinationImportMapper(Component):
    _inherit = 'prestashop.product.combination.mapper'

    @property
    def from_main(self):
        mappings = super(DimensionsProductCombinationImportMapper, self
                         ).from_main[:]
        return mappings + [
            'width',
            'height',
            'length',
        ]
