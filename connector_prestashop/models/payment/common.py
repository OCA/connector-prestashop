# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceDict
except ImportError:
    _logger.debug('Can not `from prestapyt import PrestaShopWebServiceDict.')


@prestashop
class PaymentMethodAdapter(GenericAdapter):
    _model_name = 'payment.method'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def search(self, filters=None):
        api = PrestaShopWebServiceDict(
            self.prestashop.api_url, self.prestashop.webservice_key)
        res = api.get(self._prestashop_model, options=filters)
        methods = res[self._prestashop_model][self._export_node_name]
        if isinstance(methods, dict):
            return [methods]
        return methods
