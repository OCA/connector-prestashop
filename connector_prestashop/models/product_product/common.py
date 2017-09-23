# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from odoo.addons.queue_job.job import job
from ...components.backend_adapter import GenericAdapter
from ...backend import prestashop
from exporter import CombinationInventoryExporter


class ProductProduct(models.Model):
    _inherit = 'product.product'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='odoo_id',
        copy=False,
        string='PrestaShop Bindings',
    )
    prestashop_combinations_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='odoo_id',
        string='PrestaShop Bindings (combinations)',
    )
    default_on = fields.Boolean(string='Default On')
    impact_price = fields.Float(
        string="Price Impact",
        digits=dp.get_precision('Product Price')
    )

    @api.multi
    def update_prestashop_qty(self):
        for product in self:
            if product.product_variant_count > 1:
                # Recompute qty in combination binding
                for combination_binding in product.prestashop_bind_ids:
                    combination_binding.recompute_prestashop_qty()
            # Recompute qty in product template binding if any combination
            # if modified
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

    @api.multi
    @api.depends('impact_price', 'product_tmpl_id.list_price')
    def _compute_lst_price(self):
        for product in self:
            price = product.list_price + product.impact_price
            if 'uom' in self.env.context:
                # `uos_id` comes from `product_uos`
                # which could be not installed
                uom = hasattr(product, 'uos_id') \
                    and product.uos_id or product.uom_id
                price = uom._compute_price(
                    product.uom_id.id, price, self.env.context['uom'])
            product.lst_price = price

    lst_price = fields.Float(
        compute='_compute_lst_price')

    @api.multi
    def _set_variants_default_on(self, default_on_list=None):
        if self.env.context.get('skip_check_default_variant', False):
            return True
        templates = self.mapped('product_tmpl_id')
        for template in templates:
            variants = template.with_context(
                skip_check_default_variant=True
            ).product_variant_ids.filtered('default_on')
            if not variants:
                active_variants = template.with_context(
                    skip_check_default_variant=True
                ).product_variant_ids.filtered('active')
                active_variants[:1].write({'default_on': True})
            elif len(variants) > 1:
                if default_on_list:
                    variants.filtered(
                        lambda x: x.id not in default_on_list
                    ).write({'default_on': False})
                else:
                    variants[1:].write({'default_on': False})

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        res._set_variants_default_on()
        return res

    @api.multi
    def write(self, vals):
        if not vals.get('active', True):
            vals['default_on'] = False
        res = super(ProductProduct, self).write(vals)
        default_on_list = vals.get('default_on', False) and self.ids or []
        self._set_variants_default_on(default_on_list)
        return res

    @api.multi
    def unlink(self):
        self.write({
            'default_on': False,
            'active': False
        })
        res = super(ProductProduct, self).unlink()
        return res

    @api.multi
    def open_product_template(self):
        """
        Utility method used to add an "Open Product Template"
        button in product.product views
        """
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'form',
                'res_id': self.product_tmpl_id.id,
                'target': 'new',
                'flags': {'form': {'action_buttons': True}}}


class PrestashopProductCombination(models.Model):
    _name = 'prestashop.product.combination'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.product': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    main_template_id = fields.Many2one(
        comodel_name='prestashop.product.template',
        string='Main Template',
        required=True,
        ondelete='cascade',
    )
    quantity = fields.Float(
        string='Computed Quantity',
        help='Last computed quantity to send on PrestaShop.'
    )
    reference = fields.Char(string='Original reference')

    @api.multi
    def recompute_prestashop_qty(self):
        # group products by backend
        backends = defaultdict(set)
        for product in self:
            backends[product.backend_id].add(product.id)

        for backend, product_ids in backends.iteritems():
            products = self.browse(product_ids)
            products._recompute_prestashop_qty_backend(backend)
        return True

    @api.multi
    def _recompute_prestashop_qty_backend(self, backend):
        locations = backend._get_locations_for_stock_quantities()
        self_loc = self.with_context(location=locations.ids,
                                     compute_child=False)
        for product_binding in self_loc:
            new_qty = product_binding._prestashop_qty()
            if product_binding.quantity != new_qty:
                product_binding.quantity = new_qty
        return True

    def _prestashop_qty(self):
        return self.qty_available

    @job(default_channel='root.prestashop')
    def export_inventory(self, backend, fields=None, **kwargs):
        """ Export the inventory configuration and quantity of a product. """
        env = backend.get_environment(self._name)
        inventory_exporter = env.get_connector_unit(
            CombinationInventoryExporter)
        return inventory_exporter.run(self.id, fields, **kwargs)

    @api.model
    @job(default_channel='root.prestashop')
    def export_product_quantities(self, backend):
        self.search([
            ('backend_id', 'in', backend.ids),
        ]).recompute_prestashop_qty()


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination.option',
        inverse_name='odoo_id',
        string='PrestaShop Bindings (combinations)',
    )


class PrestashopProductCombinationOption(models.Model):
    _name = 'prestashop.product.combination.option'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.attribute': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_position = fields.Integer('PrestaShop Position')
    group_type = fields.Selection([
        ('color', 'Color'),
        ('radio', 'Radio'),
        ('select', 'Select')], string='Type', default='select')
    public_name = fields.Char(string='Public Name', translate=True)


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination.option.value',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopProductCombinationOptionValue(models.Model):
    _name = 'prestashop.product.combination.option.value'
    _inherit = 'prestashop.binding'
    _inherits = {'product.attribute.value': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Attribute',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_position = fields.Integer(
        string='PrestaShop Position',
        default=1,
    )
    id_attribute_group = fields.Many2one(
        comodel_name='prestashop.product.combination.option')


@prestashop
class ProductCombinationAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination'
    _prestashop_model = 'combinations'
    _export_node_name = 'combination'


@prestashop
class ProductCombinationOptionAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination.option'
    _prestashop_model = 'product_options'
    _export_node_name = 'product_options'
