# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector_prestashop.unit.binder import (
    PrestashopBinder as PSBinder)
from openerp.addons.connector_prestashop.backend import prestashop


@prestashop(replacing=PSBinder)
class PrestashopBinder(PSBinder):
    _model_name = PSBinder._model_name + ['prestashop.specific.price']
