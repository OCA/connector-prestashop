# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        versions = super(PrestashopBackend, self)._select_versions()
        versions.append(('1.5-myversion', '1.5 My Version'))
        return versions

    version = fields.Selection(
        _select_versions,
        string='Version',
        required=True)
