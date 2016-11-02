# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.addons.connector.backend as backend


prestashop = backend.Backend('prestashop')
# version < 1.6.0.9
prestashop1500 = backend.Backend(parent=prestashop, version='1.5')
# version 1.6.0.9 - 1.6.0.10
prestashop1609 = backend.Backend(parent=prestashop, version='1.6.0.9')
# version >= 1.6.0.11
prestashop16011 = backend.Backend(parent=prestashop, version='1.6.0.11')
prestashop1612 = backend.Backend(parent=prestashop, version='1.6.1.2')
