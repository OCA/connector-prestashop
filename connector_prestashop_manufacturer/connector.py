# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models


class connector_prestashop_manufacturer(models.AbstractModel):
    """Empty model used to know if the module is installed on the
    database.

    If the model is in the registry, the module is installed.
    """
    _name = 'connector_prestashop_manufacturer.installed'
