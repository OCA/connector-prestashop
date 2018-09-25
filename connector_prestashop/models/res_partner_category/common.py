# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.partner.category',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
        readonly=True,
    )


class PrestashopResPartnerCategory(models.Model):
    _name = 'prestashop.res.partner.category'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'res.partner.category': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='res.partner.category',
        string='Partner Category',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )

    # TODO add prestashop shop when the field will be available in the api.
    # we have reported the bug for it
    # see http://forge.prestashop.com/browse/PSCFV-8284
    # 2016-10-13 UPDATE: the bug has been fixed since a while:
    # check if we can drop this!


class PartnerCategoryAdapter(Component):
    _name = 'prestashop.res.partner.category.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.res.partner.category'
    _prestashop_model = 'groups'
