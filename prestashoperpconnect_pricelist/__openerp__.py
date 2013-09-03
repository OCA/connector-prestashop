# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_pricelist for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#     All Rights Reserved
#     @author David BEAL <david.beal@akretion.com>
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
    'version': '0.1',
    'category': '',
    'sequence': 10,
    'summary': "Synchronise pricelists with PrestaShop",
    'description': """
Synchronise pricelists defined in OpenERP with PrestaShop:

How to :

- follow prestashoperpconnect intructions
- import customers
- define a pricelist in your imported shop (from PrestaShop) in OpenERP
- modify items in each pricelist defined above to active synchronisation :

    * each item record creation trigger a record creation in 'prestashop.product.pricelist.item'
    * each item record update trigger an record update in 'prestashop.product.pricelist.item'
    * each item record deletion trigger an deletion in this model
    * each modification in this model trigger a synchronisation with prestashop
    """,
    'author': 'akretion',
    'website': 'http://www.akretion.com',
    'depends': [
        'prestashoperpconnect', 'pricelist_builder_customer_attribute'
        ],
    'data': [
        'pricelist_view.xml',
        'sale_view.xml',
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
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
