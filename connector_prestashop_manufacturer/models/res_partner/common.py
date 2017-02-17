# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from openerp.addons.connector_prestashop.unit.backend_adapter import \
    GenericAdapter
from openerp.addons.connector_prestashop.backend import prestashop


class ResPartner(models.Model):
    _inherit = "res.partner"

    prestashop_manufacturer_bind_ids = fields.One2many(
        comodel_name='prestashop.manufacturer',
        inverse_name='odoo_id',
        string='PrestaShop Manufacturer Binding',
    )

    prestashop_manufacturer_address_bind_ids = fields.One2many(
        comodel_name='prestashop.manufacturer.address',
        inverse_name='odoo_id',
        string='PrestaShop Manufacturer Address Binding',
    )


class PrestashopManufacturer(models.Model):
    _name = 'prestashop.manufacturer'
    _description = 'PrestaShop Manufacturers'
    _inherit = [
        'prestashop.binding.odoo',
        'prestashop.partner.mixin',
    ]
    _inherits = {'res.partner': 'odoo_id'}

    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        readonly=True,
    )
    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
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


class PrestashopManufacturerAddress(models.Model):
    _name = 'prestashop.manufacturer.address'
    _inherit = [
        'prestashop.binding.odoo',
        'prestashop.address.mixin',
    ]
    _inherits = {'res.partner': 'odoo_id'}
    _rec_name = 'odoo_id'

    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_partner_id = fields.Many2one(
        comodel_name='prestashop.manufacturer',
        string='PrestaShop Manufacturer',
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


@prestashop
class ManufacturerAdapter(GenericAdapter):
    _model_name = 'prestashop.manufacturer'
    _prestashop_model = 'manufacturers'
    _export_node_name = 'manufacturer'
    _export_node_name_res = 'manufacturer'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        return super(ManufacturerAdapter, self).search(filters)


@prestashop
class ManufacturerAddressAdapter(GenericAdapter):
    _model_name = 'prestashop.manufacturer.address'
    _prestashop_model = 'addresses'
    _export_node_name = 'address'
    _export_node_name_res = 'address'
