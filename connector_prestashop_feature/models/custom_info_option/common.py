# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from openerp.addons.connector_prestashop.unit.backend_adapter import \
    GenericAdapter
from openerp.addons.connector_prestashop.backend import prestashop


class PrestashopProductFeatureValues(models.Model):
    _name = 'prestashop.product.feature.values'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'custom.info.option': 'odoo_id'}
    _description = 'PrestaShop Product Feature Values'

    odoo_id = fields.Many2one(
        comodel_name='custom.info.option',
        string='Product Feature Values',
        required=True,
        ondelete='cascade',
    )
    value = fields.Char(
        string='Name in PrestaShop',
    )
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )


class ProductCustomInfoOption(models.Model):
    _inherit = "custom.info.option"

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.feature.values',
        inverse_name='odoo_id',
        string='PrestaShop Feature Values Binding',
    )


@prestashop
class ProductFeatureValuesAdapter(GenericAdapter):
    _model_name = 'prestashop.product.feature.values'
    _prestashop_model = 'product_feature_values'
    _export_node_name = 'product_feature_values'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        return super(ProductFeatureValuesAdapter, self).search(filters)
