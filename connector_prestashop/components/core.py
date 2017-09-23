# -*- coding: utf-8 -*-
# © 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import AbstractComponent


class BasePrestaShopConnectorComponent(AbstractComponent):
    """ Base PrestaShop Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.prestashop.connector'
    _inherit = 'base.connector'
    _collection = 'prestashop.backend'

