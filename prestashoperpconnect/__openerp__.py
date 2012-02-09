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
    "name" : "Prestashop e-commerce",
    "version" : "1.0",
    "depends" : [
                 "product",
#                 "product_m2mcategories",
#                 'delivery',
                 "base_sale_multichannels",
#                 "product_images_olbs",
                ],
    "author" : "PrestashopERPconnect Core Editors",
    "description": """Prestashop E-commerce management
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
        'prestashoperpconnect_menu.xml',
        'board_prestashoperpconnect_view.xml',
        'settings/external.referential.type.csv',
        'settings/1.5.0.0/external.referential.version.csv',
        'settings/1.5.0.0/external.mapping.template.csv',
        'settings/1.5.0.0/res.partner.address/external.mappinglines.template.csv',
        'settings/1.5.0.0/res.partner/external.mappinglines.template.csv',
        'settings/1.5.0.0/product.product/external.mappinglines.template.csv',
        'settings/1.5.0.0/sale.order/external.mappinglines.template.csv',
            
    ],
    "active": False,
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

