# Copyright 2018 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductCombinationDeleter(Component):
    _name = "prestashop.product.combination.deleter"
    _inherit = "prestashop.deleter"
    _apply_on = "prestashop.product.combination"


class ProductCombinationOptionDeleter(Component):
    _name = "prestashop.product.combination.option.deleter"
    _inherit = "prestashop.deleter"
    _apply_on = [
        "prestashop.product.combination.option",
        "prestashop.product.combination.option.value",
    ]
