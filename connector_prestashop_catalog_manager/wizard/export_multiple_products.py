# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import unicodedata
import re

try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None


def get_slug(name):
    if slugify_lib:
        try:
            return slugify_lib.slugify(name)
        except TypeError:
            pass
    uni = unicodedata.normalize('NFKD', name).encode(
        'ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[\W_]', ' ', uni).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


class ExportMultipleProducts(models.TransientModel):
    _name = 'export.multiple.products'

    def _default_backend(self):
        return self.env['prestashop.backend'].search([], limit=1).id

    def _default_shop(self):
        return self.env['prestashop.shop'].search([], limit=1).id

    name = fields.Many2one(
        comodel_name='prestashop.backend',
        default=_default_backend,
        string='Backend',
    )
    shop = fields.Many2one(
        comodel_name='prestashop.shop',
        default=_default_shop,
        string='Shop',
    )

    def _parent_length(self, categ):
        if not categ.parent_id:
            return 1
        else:
            return 1 + self._parent_length(categ.parent_id)

    def _set_main_category(self, product):
        if product.categ_ids and product.categ_id.parent_id:
            max_parent = {'length': 0}
            for categ in product.categ_ids:
                parent_length = self._parent_length(categ.parent_id)
                if parent_length > max_parent['length']:
                    max_parent = {'categ_id': categ.id,
                                  'length': parent_length}
            categ_length = self._parent_length(product.categ_id.parent_id)
            if categ_length < parent_length:
                if product.categ_id.id not in product.categ_ids.ids:
                    product.write({
                        'categ_ids': [(4, product.categ_id.id)],
                    })
                    product.write({
                        'categ_id': max_parent['categ_id'],
                        'categ_ids': [(3, max_parent['categ_id'])]
                    })
                else:
                    product.write({
                        'categ_id': max_parent['categ_id'],
                        'categ_ids': [(3, max_parent['categ_id'])],
                    })

    @api.multi
    def set_category(self):
        product_obj = self.env['product.template']
        for product in product_obj.browse(self.env.context['active_ids']):
            self._set_main_category(product)

    def _check_images(self, product):
        for variant in product.product_variant_ids:
            for image in variant.image_ids:
                if image.owner_id != product.id:
                    image.product_id = product

    def _check_category(self, product):
        if not (product.categ_id):
            return False
        return True

    def _check_variants(self, product):
        if len(product.product_variant_ids) == 1:
            return True
        if (len(product.product_variant_ids) > 1 and
                not product.attribute_line_ids):
            check_count = reduce(
                lambda x, y: x * y, map(lambda x: len(x.value_ids),
                                        product.attribute_line_ids))
            if check_count < len(product.product_variant_ids):
                return False
        return True

    @api.multi
    def export_variant_stock(self):
        template_obj = self.env['product.template']
        products = template_obj.browse(self.env.context['active_ids'])
        products.update_prestashop_quantities()

    @api.multi
    def export_products(self):
        self.ensure_one()
        product_obj = self.env['product.template']
        presta_tmpl_obj = self.env['prestashop.product.template']
        for product in product_obj.browse(self.env.context['active_ids']):
            presta_tmpl = presta_tmpl_obj.search([
                ('odoo_id', '=', product.id),
                ('backend_id', '=', self.name.id),
                ('default_shop_id', '=', self.shop.id),
            ])
            if not presta_tmpl:
                self._check_images(product)
                cat = self._check_category(product)
                var = self._check_variants(product)
                if not(var and cat):
                    continue
                presta_tmpl_obj.create({
                    'backend_id': self.name.id,
                    'default_shop_id': self.shop.id,
                    'link_rewrite': get_slug(product.name),
                    'odoo_id': product.id,
                })
            else:
                for tmpl in presta_tmpl:
                    if ' ' in tmpl.link_rewrite:
                        tmpl.link_rewrite = get_slug(tmpl.link_rewrite)
