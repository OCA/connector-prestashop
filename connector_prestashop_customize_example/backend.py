# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import openerp.addons.connector.backend as backend
import openerp.addons.connector_prestashop.backend as prestashop_backend

prestashop_myversion = backend.Backend(
    parent=prestashop_backend.prestashop1500, version='1.5-myversion')
