# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.connector.backend as backend


prestashop = backend.Backend('prestashop')
# version < 1.6.0.9
prestashop_1_5_0_0 = backend.Backend(parent=prestashop, version='1.5')
# version 1.6.0.9 - 1.6.0.10
prestashop_1_6_0_9 = backend.Backend(parent=prestashop, version='1.6.0.9')
# version >= 1.6.0.11
prestashop_1_6_0_11 = backend.Backend(parent=prestashop, version='1.6.0.11')
# version >= 1.6.1.2
prestashop_1_6_1_2 = backend.Backend(parent=prestashop, version='1.6.1.2')
