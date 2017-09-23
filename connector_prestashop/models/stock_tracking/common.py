# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from ...components.backend_adapter import GenericAdapter
from ...backend import prestashop


@prestashop
class OrderCarriers(GenericAdapter):
    _model_name = '__not_exit_prestashop.order_carrier'
    _prestashop_model = 'order_carriers'
    _export_node_name = 'order_carrier'
