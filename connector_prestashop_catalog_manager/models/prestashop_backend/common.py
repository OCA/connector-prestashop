# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    prestashop_image_to_url = fields.Boolean(
        string="PrestaShop Image Storage Url",
        help="If this field is checked, PrestaShop images are loaded by url"
             "instead Database",
        default=True
    )
