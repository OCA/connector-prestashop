# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.partner',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
    )
    prestashop_address_bind_ids = fields.One2many(
        comodel_name='prestashop.address',
        inverse_name='openerp_id',
        string='PrestaShop Address Bindings',
    )


class PrestashopResRartner(models.Model):
    _name = 'prestashop.res.partner'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    _rec_name = 'shop_group_id'

    openerp_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        related='shop_group_id.backend_id',
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        store=True,
        readonly=True,
    )
    shop_group_id = fields.Many2one(
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
        required=True,
        ondelete='restrict',
    )
    shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='PrestaShop Shop',
    )
    group_ids = fields.Many2many(
        comodel_name='prestashop.res.partner.category',
        relation='prestashop_category_partner',
        column1='partner_id',
        column2='category_id',
        string='PrestaShop Groups',
    )
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )
    newsletter = fields.Boolean(string='Newsletter')
    default_category_id = fields.Many2one(
        comodel_name='prestashop.res.partner.category',
        string='PrestaShop default category',
        help="This field is synchronized with the field "
        "'Default customer group' in PrestaShop."
    )
    birthday = fields.Date(string='Birthday')
    company = fields.Char(string='Company')
    prestashop_address_bind_ids = fields.One2many(
        comodel_name='prestashop.address',
        inverse_name='openerp_id',
        string='PrestaShop Address Bindings',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]


class PrestashopAddress(models.Model):
    _name = 'prestashop.address'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    _rec_name = 'backend_id'

    @api.multi
    @api.depends(
        'prestashop_partner_id',
        'prestashop_partner_id.backend_id',
        'prestashop_partner_id.shop_group_id',
        )
    def _compute_backend_id(self):
        for address in self:
            address.backend_id = address.prestashop_partner_id.backend_id.id

    @api.multi
    @api.depends('prestashop_partner_id',
                 'prestashop_partner_id.shop_group_id')
    def _compute_shop_group_id(self):
        for address in self:
            address.shop_group_id = (
                address.prestashop_partner_id.shop_group_id.id)

    openerp_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
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
    prestashop_partner_id = fields.Many2one(
        comodel_name='prestashop.res.partner',
        string='PrestaShop Partner',
        required=True,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        compute='_compute_backend_id',
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        store=True,
    )
    shop_group_id = fields.Many2one(
        compute='_compute_shop_group_id',
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
        store=True,
    )
    vat_number = fields.Char('PrestaShop VAT')

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]


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
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]
    # TODO add prestashop shop when the field will be available in the api.
    # we have reported the bug for it
    # see http://forge.prestashop.com/browse/PSCFV-8284
