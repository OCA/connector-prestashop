# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from ...backend import prestashop


@prestashop
class OrderCarriers(Component):
    _name = 'prestashop.order_carrier.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = '__not_exit_prestashop.order_carrier'
    _prestashop_model = 'order_carriers'
    _export_node_name = 'order_carrier'
