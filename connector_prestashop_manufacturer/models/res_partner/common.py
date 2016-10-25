# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from openerp.addons.connector_prestashop.unit.backend_adapter import \
    GenericAdapter
from openerp.addons.connector_prestashop.backend import prestashop


class PrestashopManufacturer(models.Model):
    _name = 'prestashop.manufacturer'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'res.partner': 'odoo_id'}
    _description = 'PrestaShop Manufacturers'

    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Manufacturer',
        required=True,
        ondelete='cascade',
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
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )


class Manufacturer(models.Model):
    _inherit = "res.partner"

    prestashop_manufacturer_bind_ids = fields.One2many(
        comodel_name='prestashop.manufacturer',
        inverse_name='odoo_id',
        string='PrestaShop Manufacturer Binding',
    )


@prestashop
class ManufacturerAdapter(GenericAdapter):
    _model_name = 'prestashop.manufacturer'
    _prestashop_model = 'manufacturers'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        return super(ManufacturerAdapter, self).search(filters)
