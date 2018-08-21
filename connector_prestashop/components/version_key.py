# -*- coding: utf-8 -*-
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.addons.component.core import Component


class VersionKeyModel(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = '_prestashop.version.key'


class VersionKey(Component):
    _name = '_prestashop.version.key'
    _apply_on = '_prestashop.version.key'
    _usage = 'prestashop.version.key'

    keys = {
        'messages': 'customer_messages',
    }

    def get_key(self, key):
        return self.keys.get(key) or key


class VersionKey_1_6_0_9(Component):
    _name = '_prestashop.version.key.1.6.0.9'
    _inherit = '_prestashop.version.key'
    _usage = 'prestashop.version.key.1.6.0.9'

    keys = {
        'product_option_value': 'product_option_values',
        'category': 'categories',
        'order_slip': 'order_slips',
        'order_slip_detail': 'order_slip_details',
        'group': 'groups',
        'order_row': 'order_rows',
        'tax': 'taxes',
        'image': 'images',
        'combinations': 'combinations',
        'tag': 'tags',
        'manufacturers': 'manufacturers',
    }


class VersionKey_1_6_1_2(Component):
    _name = '_prestashop.version.key.1.6.1.2'
    _inherit = '_prestashop.version.key'
    _usage = 'prestashop.version.key.1.6.1.2'

    # keys checked in 1.6.1.9:
    # * customer_messages
    # * order_slip
    # * order_slip_detail

    keys = {
        'product_option_value': 'product_option_value',
        'category': 'category',
        'image': 'image',
        'order_slip': 'order_slip',
        'order_slip_detail': 'order_slip_detail',
        'group': 'group',
        'order_row': 'order_row',
        'tax': 'taxes',
        'combinations': 'combination',
        'product_features': 'product_feature',
        'tag': 'tag',
        'messages': 'customer_messages',
        'manufacturers': 'manufacturers',
    }
