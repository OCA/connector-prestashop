# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector_prestashop.unit.binder import PrestashopBinder
from openerp.addons.connector_prestashop.backend import prestashop


@prestashop
class PrestashopBinderManufacturer(PrestashopBinder):
    _model_name = 'prestashop.manufacturer'
