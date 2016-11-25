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


class PrestashopExportCategory(models.TransientModel):
    _name = 'wiz.prestashop.export.category'

    def _default_backend(self):
        return self.env['prestashop.backend'].search([], limit=1).id

    def _default_shop(self):
        return self.env['prestashop.shop'].search([], limit=1).id

    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        default=_default_backend,
        string='Backend',
    )
    shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        default=_default_shop,
        string='Shop',
    )

    @api.multi
    def export_categories(self):
        self.ensure_one()
        category_obj = self.env['product.category']
        ps_category_obj = self.env['prestashop.product.category']
        for category in category_obj.browse(self.env.context['active_ids']):
            ps_category = ps_category_obj.search([
                ('odoo_id', '=', category.id),
                ('backend_id', '=', self.backend_id.id),
                ('default_shop_id', '=', self.shop_id.id),
            ])
            if not ps_category:
                ps_category_obj.create({
                    'backend_id': self.backend_id.id,
                    'default_shop_id': self.shop_id.id,
                    'link_rewrite': get_slug(category.name),
                    'odoo_id': category.id,
                })
