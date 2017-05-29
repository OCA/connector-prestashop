# -*- coding: utf-8 -*-
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.connector.connector import ConnectorUnit
from ..backend import prestashop, prestashop_1_6_0_9, prestashop_1_6_1_2


@prestashop
class VersionKey(ConnectorUnit):
    _model_name = '_prestashop.version.key'

    keys = {}

    def get_key(self, key):
        return self.keys.get(key) or key


@prestashop_1_6_0_9
class VersionKey_1_6_0_9(VersionKey):

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


@prestashop_1_6_1_2
class VersionKey_1_6_1_2(VersionKey):

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
