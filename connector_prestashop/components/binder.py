# -*- coding: utf-8 -*-
# © 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PrestashopModelBinder(Component):
    """ Bind records and give odoo/prestashop ids correspondence

    Binding models are models called ``prestashop.{normal_model}``,
    like ``prestashop.res.partner`` or ``prestashop.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Prestashop ID, the ID of the Prestashop Backend and the additional
    fields belonging to the Prestashop instance.
    """
    _name = 'prestashop.binder'
    _inherit = ['base.binder', 'base.prestashop.connector']
    _external_field = 'prestashop_id'

    _apply_on = [
        'prestashop.shop.group',
        'prestashop.shop',
        'prestashop.res.partner',
        'prestashop.address',
        'prestashop.res.partner.category',
        'prestashop.res.lang',
        'prestashop.res.country',
        'prestashop.res.currency',
        'prestashop.account.tax',
        'prestashop.account.tax.group',
        'prestashop.product.category',
        'prestashop.product.image',
        'prestashop.product.template',
        'prestashop.product.combination',
        'prestashop.product.combination.option',
        'prestashop.product.combination.option.value',
        'prestashop.sale.order',
        'prestashop.sale.order.state',
        'prestashop.delivery.carrier',
        'prestashop.refund',
        'prestashop.supplier',
        'prestashop.product.supplierinfo',
        'prestashop.mail.message',
        'prestashop.groups.pricelist',
    ]
