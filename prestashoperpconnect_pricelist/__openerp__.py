# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#     All Rights Reserved
#     @author David BEAL <david.beal@akretion.com>
#     Sébastien BEAU <sebastien.beau@akretion.com>
#     Guewen Baconnier (camptocamp)
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

{
    'name': 'prestashoperpconnect_pricelist',
    'version': '0.2',
    'category': '',
    'sequence': 10,
    'summary': "Synchronise pricelists with PrestaShop",
    'description': """
Synchronise pricelists defined in OpenERP with PrestaShop:
==========================================================

How to:
-------
* follow prestashoperpconnect intructions
* import customers
* import products
* define a pricelist in your imported shop (from PrestaShop) in OpenERP
* modify items in each pricelist defined above to active synchronisation :

    * each item record creation/update/deletion trigger a record
        creation/update/deletion in 'prestashop.product.pricelist.item'
    * each modification in this model trigger a synchronisation with prestashop

TODO:
-----
* put a delay between activation and desactivation of pricelist.builder

    """,
    'author': 'akretion',
    'website': 'http://www.akretion.com',
    'depends': [
        'prestashoperpconnect',
        'pricelist_builder_customer_attribute',
        ],
    'data': [
        'views/pricelist_view.xml',
        'views/sale_view.xml',
        'security/pricelist_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'images': [
    ],
    'css': [
    ],
    'js': [
    ],
    'qweb': [
    ],
}
