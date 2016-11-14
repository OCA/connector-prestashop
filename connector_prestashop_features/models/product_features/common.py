# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from openerp.addons.connector_prestashop.unit.backend_adapter import \
    GenericAdapter
from openerp.addons.connector_prestashop.backend import prestashop


class PrestashopProductFeatures(models.Model):
    _name = 'prestashop.product.features'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'custom.info.property': 'odoo_id'}
    _description = 'PrestaShop Product Features'

    odoo_id = fields.Many2one(
        comodel_name='custom.info.property',
        string='Product Features',
        required=True,
        ondelete='cascade',
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


class ProductCustomInfoProperty(models.Model):
    _inherit = "custom.info.property"

    prestashop_feature_bind_ids = fields.One2many(
        comodel_name='prestashop.product.features',
        inverse_name='odoo_id',
        string='PrestaShop Features Binding',
    )


@prestashop
class ProductFeaturesAdapter(GenericAdapter):
    _model_name = 'prestashop.product.features'
    _prestashop_model = 'product_features'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        return super(ProductFeaturesAdapter, self).search(filters)


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
    name_ext = fields.Char(
        string='Name in PrestaShop',
    )
    position = fields.Integer(
        string='Position in PrestaShop',
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

    prestashop_feature_bind_ids = fields.One2many(
        comodel_name='prestashop.product.feature.values',
        inverse_name='odoo_id',
        string='PrestaShop Feature Values Binding',
    )


@prestashop
class ProductFeatureValuesAdapter(GenericAdapter):
    _model_name = 'prestashop.product.feature.values'
    _prestashop_model = 'product_feature_values'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        return super(ProductFeatureValuesAdapter, self).search(filters)
