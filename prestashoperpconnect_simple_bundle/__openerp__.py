# -*- encoding: utf-8 -*-
##############################################################################
#
#    PrestaShopERPconnect simple bundle module for OpenERP
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
    'name': 'PrestaShopERPconnect - Simple bundle',
    'version': '1.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'description': """This module adds support for product packs in the OpenERP-PrestaShop connector. Here is how it works : when orders are imported from PrestaShop to OpenERP, OpenERP will look at the order lines. If it finds an order line which has a product ID that is not mapped to an OpenERP product and that this product is a pack, then it will query PrestaShop to get the composition of the pack and it will import the composition of the pack in the OpenERP sale order.

The use of this module requires the support for product packs in the PrestaShop webservices, which has been developped by Anatole Korczak (check http://forge.prestashop.com/browse/PSCFI-6525).

This module has been developped by Akretion (http://www.akretion.com), who is part of the PrestashopERPconnect Core Editors.
    """,
    'author': 'Akretion',
    'website': 'https://launchpad.net/prestashoperpconnect/',
    'depends': [
        'prestashoperpconnect',
        ],
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
