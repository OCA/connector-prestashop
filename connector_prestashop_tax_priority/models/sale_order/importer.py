# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class SaleOrderLineMapper(Component):
    _inherit = "prestashop.sale.order.line.mapper"

    @mapping
    def tax_id(self, record):
        tax_strategy = self.backend_record.tax_priority
        if tax_strategy == "odoo":
            return {}
        return super(SaleOrderLineMapper, self).tax_id(record)


class SaleOrderLineDiscountMapper(Component):
    _inherit = "prestashop.sale.order.discount.importer"

    @mapping
    def tax_id(self, record):
        tax_strategy = self.backend_record.tax_priority
        if tax_strategy == "odoo":
            return {}
        return super(SaleOrderLineDiscountMapper, self).tax_id(record)
