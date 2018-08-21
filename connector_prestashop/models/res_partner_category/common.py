# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.partner.category',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
        readonly=True,
    )


class PrestashopResPartnerCategory(models.Model):
    _name = 'prestashop.res.partner.category'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner.category': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='res.partner.category',
        string='Partner Category',
        required=True,
        ondelete='cascade',
    )
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'A erp record with same ID on PrestaShop already exists.'),
    ]
    # TODO add prestashop shop when the field will be available in the api.
    # we have reported the bug for it
    # see http://forge.prestashop.com/browse/PSCFV-8284


class PartnerCategoryAdapter(Component):
    _name = 'prestashop.res.partner.category.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.res.partner.category'
    _prestashop_model = 'groups'
