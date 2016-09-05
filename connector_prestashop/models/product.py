# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductImage(models.Model):
    _inherit = 'base_multi_image.image'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.image',
        inverse_name='openerp_id',
        string='PrestaShop Bindings',
    )


class PrestashopProductImage(models.Model):
    _name = 'prestashop.product.image'
    _inherit = 'prestashop.binding'
    _inherits = {'base_multi_image.image': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='base_multi_image.image',
        required=True,
        ondelete='cascade',
        string='Product image',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with same ID already exists on PrestaShop.'),
    ]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.template',
        inverse_name='openerp_id',
        copy=False,
        string='PrestaShop Bindings',
    )

    @api.multi
    def update_prestashop_quantities(self):
        for template in self:
            for prestashop_template in template.prestashop_bind_ids:
                prestashop_template.recompute_prestashop_qty()
            ps_combinations = template.product_variant_ids
            for ps_combinations in ps_combinations.prestashop_bind_ids:
                ps_combinations.recompute_prestashop_qty()
        return True


class PrestashopProductTemplate(models.Model):
    _name = 'prestashop.product.template'
    _inherit = 'prestashop.binding'
    _inherits = {'product.template': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        ondelete='cascade',
        string='Template',
    )
    # TODO FIXME what name give to field present in
    # prestashop_product_product and product_product
    always_available = fields.Boolean(
        string='Active',
        default=True,
        help='If checked, this product is considered always available')
    quantity = fields.Float(
        string='Computed Quantity',
        help="Last computed quantity to send to PrestaShop."
    )
    description_html = fields.Html(
        string='Description',
        translate=True,
        help="HTML description from PrestaShop",
    )
    description_short_html = fields.Html(
        string='Short Description',
        translate=True,
    )
    date_add = fields.Datetime(
        string='Created at (in PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated at (in PrestaShop)',
        readonly=True
    )
    default_shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='Default shop',
        required=True
    )
    link_rewrite = fields.Char(
        string='Friendly URL',
        translate=True,
    )
    available_for_order = fields.Boolean(
        string='Available for Order Taking',
        default=True,
    )
    show_price = fields.Boolean(string='Display Price', default=True)
    combinations_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='main_template_id',
        string='Combinations'
    )
    reference = fields.Char(string='Original reference')
    on_sale = fields.Boolean(string='Show on sale icon')

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]

    @api.multi
    def recompute_prestashop_qty(self):
        for product in self:
            new_qty = product._prestashop_qty()
            product.write({
                'quantity': new_qty,
            })
        return True

    def _prestashop_qty(self):
        location_id = self.backend_id.warehouse_id.lot_stock_id.id
        return self.with_context(location=location_id).qty_available


class ProductProduct(models.Model):
    _inherit = 'product.product'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='openerp_id',
        copy=False,
        string='PrestaShop Bindings',
    )

    @api.multi
    def update_prestashop_qty(self):
        for product in self:
            if product.product_variant_count > 1:
                for combination_binding in product.prestashop_bind_ids:
                    combination_binding.recompute_prestashop_qty()
            else:
                for prestashop_product in \
                        product.product_tmpl_id.prestashop_bind_ids:
                    prestashop_product.recompute_prestashop_qty()

    @api.multi
    def update_prestashop_quantities(self):
        for product in self:
            product_template = product.product_tmpl_id
            prestashop_combinations = (
                len(product_template.product_variant_ids) > 1 and
                product_template.product_variant_ids) or []
            if not prestashop_combinations:
                for prestashop_product in product_template.prestashop_bind_ids:
                    prestashop_product.recompute_prestashop_qty()
            else:
                for prestashop_combination in prestashop_combinations:
                    for combination_binding in \
                            prestashop_combination.prestashop_bind_ids:
                        combination_binding.recompute_prestashop_qty()
        return True


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    prestashop_groups_bind_ids = fields.One2many(
        comodel_name='prestashop.groups.pricelist',
        inverse_name='openerp_id',
        string='PrestaShop user groups',
    )


class PrestashopGroupsPricelist(models.Model):
    _name = 'prestashop.groups.pricelist'
    _inherit = 'prestashop.binding'
    _inherits = {'product.pricelist': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='product.pricelist',
        required=True,
        ondelete='cascade',
        string='Odoo Pricelist',
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, openerp_id)',
         'An ERP record with the same ID already exists on PrestaShop.'),
    ]
