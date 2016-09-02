# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp import fields, models

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


class PrestashopResCurrency(models.Model):
    _name = 'prestashop.res.currency'
    _inherit = 'prestashop.binding'
    _inherits = {'res.currency': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
    ]


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.currency',
        inverse_name='openerp_id',
        string='prestashop Bindings',
        readonly=True
    )


@prestashop
class ResCurrencyAdapter(GenericAdapter):
    _model_name = 'prestashop.res.currency'
    _prestashop_model = 'currencies'
