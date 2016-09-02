# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import models, fields

from ...backend import prestashop
from ...unit.backend_adapter import GenericAdapter

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
        string='Id reference',
        help="In PrestaShop, carriers with the same 'id_reference' are "
             "some copies from the first one id_reference (only the last "
             "one copied is taken account ; and the only one which "
             "synchronized with erp)"
    )
    name_ext = fields.Char(
        string='External name',
    )
    active_ext = fields.Boolean(
        string='External active',
        help="... in prestashop",
    )
    export_tracking = fields.Boolean(
        string='Export tracking numbers',
        help=" ... in prestashop",
        default=False
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
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
        required=True,
    )


@prestashop
class DeliveryCarrierAdapter(GenericAdapter):
    _model_name = 'prestashop.delivery.carrier'
    _prestashop_model = 'carriers'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        filters['filter[deleted]'] = 0

        return super(DeliveryCarrierAdapter, self).search(filters)
