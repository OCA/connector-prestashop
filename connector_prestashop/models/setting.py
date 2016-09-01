# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class PrestashopConfigSettings(models.TransientModel):
    _inherit = 'connector.config.settings'

    module_connector_prestashop_other_module = fields.Boolean(
        string="Example setting checkbox (experimental)",
        help="This installs the module connector_prestashop_... "
             "(no real action now)"
    )
