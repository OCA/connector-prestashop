# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'
    _description = 'PrestaShop Backend Configuration'
    


    tax_priority = fields.Selection(
        selection=[('prestashop', 'Use Prestashop tax mapping'),('odoo', 'Use Odoo as tax manager')],
        default='prestashop',
        string='Which conf choose for tax priority',
        required=True,
    )
