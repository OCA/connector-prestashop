# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp import fields, models

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


class PrestashopResCountry(models.Model):
    _name = 'prestashop.res.country'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'res.country': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='res.country',
        required=True,
        ondelete='cascade',
        string='Country',
        oldname='openerp_id',
    )


class ResCountry(models.Model):
    _inherit = 'res.country'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.country',
        inverse_name='odoo_id',
        readonly=True,
        string='prestashop Bindings',
    )


@prestashop
class ResCountryAdapter(GenericAdapter):
    _model_name = 'prestashop.res.country'
    _prestashop_model = 'countries'
