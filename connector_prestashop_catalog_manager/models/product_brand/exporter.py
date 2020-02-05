# -*- coding: utf-8 -*-
# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductBrandExporter(Component):
    _name = 'prestashop.product.brand.exporter'
    _inherit = 'prestashop.exporter'
    _apply_on = 'prestashop.product.brand'


class ProductBrandExportMapper(Component):
    _name = 'prestashop.product.brand.export.mapper'
    _inherit = 'translation.prestashop.export.mapper'
    _apply_on = 'prestashop.product.brand'

    direct = [
        ('name', 'name'),
    ]
