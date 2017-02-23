# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


class ResPartner(models.Model):
    _inherit = 'res.partner'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.res.partner',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    prestashop_address_bind_ids = fields.One2many(
        comodel_name='prestashop.address',
        inverse_name='odoo_id',
        string='PrestaShop Address Bindings',
    )


class PrestashopPartnerMixin(models.AbstractModel):
    _name = 'prestashop.partner.mixin'

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
    default_category_id = fields.Many2one(
        comodel_name='prestashop.res.partner.category',
        string='PrestaShop default category',
        help="This field is synchronized with the field "
        "'Default customer group' in PrestaShop."
    )
    company = fields.Char(string='Company')


class PrestashopResPartner(models.Model):
    _name = 'prestashop.res.partner'
    _inherit = [
        'prestashop.binding.odoo',
        'prestashop.partner.mixin',
    ]
    _inherits = {'res.partner': 'odoo_id'}
    _rec_name = 'shop_group_id'

    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
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
    newsletter = fields.Boolean(string='Newsletter')
    birthday = fields.Date(string='Birthday')


class PrestashopAddressMixin(models.AbstractModel):
    _name = 'prestashop.address.mixin'

    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )


class PrestashopAddress(models.Model):
    _name = 'prestashop.address'
    _inherit = [
        'prestashop.binding.odoo',
        'prestashop.address.mixin',
    ]
    _inherits = {'res.partner': 'odoo_id'}
    _rec_name = 'odoo_id'

    prestashop_partner_id = fields.Many2one(
        comodel_name='prestashop.res.partner',
        string='PrestaShop Partner',
        required=True,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        related='prestashop_partner_id.backend_id',
        store=True,
        readonly=True,
    )
    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    shop_group_id = fields.Many2one(
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
        related='prestashop_partner_id.shop_group_id',
        store=True,
        readonly=True,
    )
    vat_number = fields.Char('PrestaShop VAT')


@prestashop
class PartnerAdapter(GenericAdapter):
    _model_name = 'prestashop.res.partner'
    _prestashop_model = 'customers'


@prestashop
class PartnerAddressAdapter(GenericAdapter):
    _model_name = 'prestashop.address'
    _prestashop_model = 'addresses'
