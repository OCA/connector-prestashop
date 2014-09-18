# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_customize_example for OpenERP
#   Copyright (C) 2013 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import orm, fields


class prestashop_backend(orm.Model):
    _inherit = 'prestashop.backend'

    def _select_versions(self, cr, uid, context=None):
        """ Available versions

        Can be inherited to add custom versions.
        """
        versions = super(prestashop_backend, self)._select_versions(
            cr, uid, context=context)
        versions.append(('1.5-myversion', '1.5 My Version'))
        return versions

    _columns = {
        'version': fields.selection(
            _select_versions,
            string='Version',
            required=True),
        }
