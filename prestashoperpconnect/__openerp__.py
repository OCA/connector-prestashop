    # -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Camptocamp                                             #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
{
    "name" : "Prestashop-OpenERP connector",
    "version" : "0.1", # 0.1 codenamed "In tartiflette we trust"
    "license": "AGPL-3",
    "depends" : [
                 "product",
#                 "product_m2mcategories",
                 "base_sale_multichannels",
#                 "product_images_olbs",
                ],
    "author" : "PrestashopERPconnect Core Editors",
    "description": """This module connects OpenERP and Prestashop.

Prestashop (http://www.prestashop.com/) is a popular e-commerce plateform written in PHP/MySQL and published under the Open Software licence v3.0.

This module allows the synchronisation of the following objects between OpenERP and Prestashop :
- shop groups and shops
- currencies
- languages
- countries
- carriers
- products

Once these objects are synchronised, it will allow the import of orders, together with the related customers and addresses.

This connector uses the OpenERP modules base_sale_multichannels and base_external_referentials that bring a very sophisticated abstraction layer to build a reliable connector between OpenERP and another application. This connector requires the Prestapyt library that you can install via the command "easy_install prestapyt" (the source code of the library is managed on https://github.com/guewen/prestapyt). You also need the patch on OpenERP addons available here : https://bugs.launchpad.net/openobject-addons/+bug/930127

This connector supports Prestashop 1.5 and uses the webservices of Prestashop ; it doesn't require any plug-in in Prestashop.

This connector was started by Akretion (http://www.akretion.com/) and Camptocamp (http://www.camptocamp.com/) during a code sprint that took place in Seythenex (Haute-Savoie, France) on 6-10 February 2012. Publishing this connector as free software was possible thanks to a large R&D effort of Akretion and Camptocamp (with some help of Julius Network Solutions). Akretion and Camptocamp form the "PrestashopERPconnect Core Editors".

This connector is built on a very solid basis, but still requires deep knowledge of both OpenERP, Prestashop and the connector's internals to be deployed successfully in production. The PrestashopERPconnect Core Editors are available to help you deploy this solution for your Prestashop-based e-commerce business.
""",
    'images': [
    ],
    "website" : "https://launchpad.net/prestashoperpconnect",
    "category" : "Generic Modules",
    "complexity" : "expert",
    "init_xml" : [],
    "demo_xml" : [],
    'update_xml': [ 
        'external_referential_view.xml',
        'prestashoperpconnect_view.xml',
        'sale_view.xml',
        'sale_states_view.xml',
        'prestashoperpconnect_menu.xml',
        'board_prestashoperpconnect_view.xml',
#        'settings/external.referential.category.csv',
        'settings/external.referential.type.csv',
        'settings/1.5.0.0/external.referential.version.csv',
        'settings/1.5.0.0/external.mapping.template.csv',
        'settings/1.5.0.0/res.partner.address/external.mappinglines.template.csv',
        'settings/1.5.0.0/res.partner/external.mappinglines.template.csv',
        'settings/1.5.0.0/product.product/external.mappinglines.template.csv',
        'settings/1.5.0.0/sale.order/external.mappinglines.template.csv',
        'settings/1.5.0.0/external.shop.group/external.mappinglines.template.csv',
        'settings/1.5.0.0/sale.shop/external.mappinglines.template.csv',
        'settings/1.5.0.0/sale.order.line/external.mappinglines.template.csv',
        'settings/1.5.0.0/delivery.carrier/external.mappinglines.template.csv',
        'settings/1.4.0.0/external.referential.version.csv',
        'settings/1.4.0.0/external.mapping.template.csv',
        'settings/1.4.0.0/res.partner.address/external.mappinglines.template.csv',
        'settings/1.4.0.0/res.partner/external.mappinglines.template.csv',
        'settings/1.4.0.0/product.category/external.mappinglines.template.csv',
        'settings/1.4.0.0/product.product/external.mappinglines.template.csv',
        'settings/1.4.0.0/product.template/external.mappinglines.template.csv',
        'settings/1.4.0.0/sale.order/external.mappinglines.template.csv',
        'settings/1.4.0.0/sale.shop/external.mappinglines.template.csv',
        'settings/1.4.0.0/sale.order.line/external.mappinglines.template.csv',
        'settings/1.4.0.0/delivery.carrier/external.mappinglines.template.csv',
        'settings/1.4.0.0/sale.order.state/external.mappinglines.template.csv',
        'settings/1.4.0.0/sale.order.history/external.mappinglines.template.csv',
    ],
    "active": False,
    "installable": True,
    "application": True,
}

