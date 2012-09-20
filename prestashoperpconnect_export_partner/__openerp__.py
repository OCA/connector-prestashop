# -*- encoding: utf-8 -*-
##############################################################################
#
#    PrestaShopERPconnect export partner module for OpenERP
#    Copyright (C) 2012 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'PrestaShopERPconnect - Export partners',
    'version': '1.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'description': """This module adds support for exporting partners from OpenERP to PrestaShop.

This module has been developped by the PrestashopERPconnect Core Editors, which is composed of Akretion (http://www.akretion.com) and Camptocamp (http://www.camptocamp.com).
    """,
    'author': 'PrestashopERPconnect Core Editors',
    'website': 'https://launchpad.net/prestashoperpconnect/',
    'depends': [
        'base_sale_export_partner',
        'prestashoperpconnect',
        ],
    'init_xml': [],
    'update_xml': [
        'partner_view.xml',
        'settings/1.5.0.0/res.partner/external.mappinglines.template.csv',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
