# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import models, fields
_logger = logging.getLogger(__name__)


class PrestashopDeliveryCarrier(models.Model):
    _name = 'prestashop.delivery.carrier'
    _inherit = 'prestashop.binding'
    _inherits = {'delivery.carrier': 'openerp_id'}
    _description = 'PrestaShop Carrier'

    openerp_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery carrier',
        required=True,
        ondelete='cascade'
    )
    id_reference = fields.Integer(
        string='Reference ID',
        help="In PrestaShop, carriers can be copied with the same 'Reference "
             "ID' (only the last copied carrier will be synchronized with the "
             "ERP)"
    )
    name_ext = fields.Char(
        string='Name in PrestaShop',
    )
    active_ext = fields.Boolean(
        string='Active in PrestaShop',
    )
    export_tracking = fields.Boolean(
        string='Export tracking numbers to PrestaShop',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with same ID on PrestaShop already exists.'),
    ]


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.delivery.carrier',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        index=True,
    )
