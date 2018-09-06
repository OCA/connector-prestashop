# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PrestashopDeliveryCarrier(models.Model):
    _name = 'prestashop.delivery.carrier'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'delivery.carrier': 'odoo_id'}
    _description = 'PrestaShop Carrier'

    odoo_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery carrier',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
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
        ('prestashop_erp_uniq', 'unique(backend_id, odoo_id, id_reference)',
         'An ERP record with same ID already exists on PrestaShop with the '
         'same id_reference'),
    ]


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.delivery.carrier',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        index=True,
    )


class DeliveryCarrierAdapter(Component):
    _name = 'prestashop.delivery.carrier.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.delivery.carrier'

    _model_name = 'prestashop.delivery.carrier'
    _prestashop_model = 'carriers'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        filters['filter[deleted]'] = 0
        return super(DeliveryCarrierAdapter, self).search(filters)
