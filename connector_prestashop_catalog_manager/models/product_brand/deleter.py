# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductBrandDeleter(Component):
    _name = "prestashop.product.brand.deleter"
    _inherit = "prestashop.deleter"
    _apply_on = [
        "prestashop.product.brand",
    ]
