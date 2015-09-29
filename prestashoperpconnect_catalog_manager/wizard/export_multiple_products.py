
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2008-2013 AvanzOSC S.L. (Mikel Arregi) All Rights Reserved
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

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

    name = fields.Many2one(comodel_name='prestashop.backend', string='Backend')
    shop = fields.Many2one(comodel_name='prestashop.shop')

    @api.multi
    def export_products(self):
        self.ensure_one()
        product_obj = self.env['product.template']
        presta_tmpl_obj = self.env['prestashop.product.template']
        presta_attrs_obj = self.env['prestashop.product.combination.option']
        for product in product_obj.browse(self.env.context['active_ids']):
            for attribute in product.attribute_line_ids.mapped('attribute_id'):
                presta_attrs = attribute.prestashop_bind_ids.filtered(
                    lambda x: x.backend_id.id == self.name.id)
                if not presta_attrs:
                    attribute.write(
                        {'prestashop_bind_ids': [(
                            0, 0, {'backend_id': self.name.id,
                                   'default_shop_id': self.shop.id,
                                   'public_name': get_slug(attribute.name)})]})

            presta_tmpl = presta_tmpl_obj.search(
                [('openerp_id', '=', product.id),
                 ('backend_id', '=', self.name.id),
                 ('default_shop_id', '=', self.shop.id)])
            if not presta_tmpl:
                presta_tmpl_obj.create(
                    {'backend_id': self.name.id,
                     'default_shop_id': self.shop.id,
                     'link_rewrite': get_slug(product.name),
                     'openerp_id': product.id})
            else:
                for tmpl in presta_tmpl:
                    if ' ' in tmpl.link_rewrite:
                        tmpl.link_rewrite = get_slug(tmpl.link_rewrite)
