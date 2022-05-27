# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import pytz
from odoo import _, fields
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import FailedJobError, NothingToDoJob
from odoo.addons.connector_ecommerce.components.sale_order_onchange import (
    SaleOrderOnChange,
)

from datetime import datetime, timedelta
from decimal import Decimal
import logging
_logger = logging.getLogger(__name__)


class SaleOrderLineMapper(Component):
    _inherit = 'prestashop.sale.order.line.mapper'

    @mapping
    def tax_id(self, record):
        tax_strategy = self.backend_record.tax_priority
        if tax_strategy == 'odoo' :
            return {}
        return super(SaleOrderLineMapper, self).tax_id(record)


class SaleOrderLineDiscountMapper(Component):
    _inherit = 'prestashop.sale.order.discount.importer'


    @mapping
    def tax_id(self, record):
        tax_strategy = self.backend_record.tax_priority
        if tax_strategy == 'odoo' :
            return {}
        return super(SaleOrderLineDiscountMapper, self).tax_id(record)

