# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class DimensionsProductTemplateImportMapper(Component):
    _inherit = 'prestashop.product.template.mapper'

    @property
    def direct(self):
        mappings = super(DimensionsProductTemplateImportMapper, self).direct[:]
        return mappings + [
            ('width', 'width'),
            ('height', 'height'),
            ('depth', 'length'),
        ]
