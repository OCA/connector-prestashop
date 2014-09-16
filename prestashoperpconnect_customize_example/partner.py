# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_customize_exemple for OpenERP
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
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.prestashoperpconnect.unit.mapper import PartnerImportMapper
from .backend import prestashop_myversion


class prestashop_res_partner(orm.Model):
    _inherit = 'prestashop.res.partner'

    _columns = {
        'prestashop_created_date': fields.datetime(
            'PrestaShop create date',
            readonly=True
        ),
        }


@prestashop_myversion
class MyPartnerImportMapper(PartnerImportMapper):
    _model_name = 'prestashop.res.partner'

    direct = PartnerImportMapper.direct + \
        [('prestashop_created_date', 'date_add')]

    @mapping
    def name(self, record):
        res = super(MyPartnerImportMapper, self).name(record)
        res['name'] = "Il est pit ton nom : %s" % res['name']
        return res
