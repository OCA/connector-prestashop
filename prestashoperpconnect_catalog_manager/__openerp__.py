# -*- encoding: utf-8 -*-
###############################################################################
#
#   Prestashop_catalog_manager for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>. All Rights Reserved
#   @author : Sébastien BEAU <sebastien.beau@akretion.com>
#             Benoît GUILLOT <benoit.guillot@akretion.com>
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

{
    "name" : "Prestashop-OpenERP connector",
    "version" : "0.2", # 0.1 codenamed "In tartiflette we trust"
    "license": "AGPL-3",
    "depends" : [
                 "prestashoperpconnect",
                 "product_images_sync",
                 "product_links",
                ],
    "author" : "PrestashopERPconnect Core Editors",
    "description": """This module is an extention for PrestashopERPconnect.

With this module you will be able to manage your catalog directly from OpenERP. You can :
- create/modify custom attributs and options in OpenERP and push then in pretashop.
- create/modify products and push then in prestashop.

TODO :
- create/modify category and push then in prestashop.
- create/modify image and push then in prestashop.
""",
    'images': [
    ],
    "website" : "https://launchpad.net/prestashoperpconnect",
    "category" : "Generic Modules",
    "complexity" : "expert",
    "init_xml" : [],
    "demo_xml" : [],
    'update_xml': [
    ],
    "active": False,
    "installable": True,
    "application": True,
}
