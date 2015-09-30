# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright (C) 2015 Tech-Receptives(<http://www.tech-receptives.com>)
#    Copyright 2013 Camptocamp SA
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    @author: Guewen Baconnier
#    @author Parthiv Patel <parthiv@techreceptives.com>
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
    "name": "Prestashop-OpenERP connector New Generation",
    # 0.1 codenamed "In tartiflette we trust"
    # 0.2 codenamed "In La Sambuy we ski"
    "version": "0.3",
    "license": "AGPL-3",
    "depends": [
        "product",
        "product_m2mcategories",
        "connector_ecommerce",
        "product_images",
        "purchase",
    ],
    "external_dependencies": {
        'python': ["unidecode"],
    },
    "author": "PrestashopERPconnect Core Editors",
    "description": """This module connects OpenERP and Prestashop.

Prestashop (http://www.prestashop.com/) is a popular e-commerce plateform
written in PHP/MySQL and published under the Open Software licence v3.0.

This module allows the synchronisation of the following objects between OpenERP
and Prestashop :
- shop groups and shops
- currencies
- languages
- countries
- carriers
- products

Once these objects are synchronised, it will allow the import of orders,
together with the related customers and addresses.

This connector supports Prestashop 1.5 and uses the webservices of Prestashop ;
it doesn't require any plug-in in Prestashop.

This connector was started by Akretion (http://www.akretion.com/) and
Camptocamp(http://www.camptocamp.com/) during a code sprint that took place in
Seythenex(Haute-Savoie, France) on 6-10 February 2012. Publishing this
connector as free software was possible thanks to a large R&D effort of
Akretion and Camptocamp (with some help of Julius Network Solutions). Akretion
and Camptocamp form the "PrestashopERPconnect Core Editors".

This connector is built on a very solid basis, but still requires deep
knowledge of both OpenERP, Prestashop and the connector's internals to be
deployed successfully in production. The PrestashopERPconnect Core Editors are
available to help you deploy this solution for your Prestashop-based e-commerce
business.
""",
    'images': [
    ],
    "website": "https://launchpad.net/prestashoperpconnect",
    "category": "Connector",
    "complexity": "expert",
    "demo": [],
    'data': [
        'data/cron.xml',
        'data/product_decimal_precision.xml',

        'prestashop_model_view.xml',
        'product_view.xml',
        'delivery_view.xml',
        'prestashoperpconnect_menu.xml',
        'partner_view.xml',
        'sale_view.xml',
        'setting_view.xml',

        'security/ir.model.access.csv',
        'security/prestashop_security.xml',
        'ecommerce_data.xml',
    ],
    "active": True,
    "installable": True,
    "application": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
