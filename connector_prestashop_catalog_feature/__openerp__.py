# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Prestashop Catalog Manager Features",
    "version": "9.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "connector_prestashop_catalog_manager",
        "connector_prestashop_feature",
    ],
    'website': 'https://odoo-community.org/',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    "category": "Connector",
    "data": [
        'views/custom_info_property_view.xml',
        'views/custom_info_option_view.xml',
        'wizard/export_feature_view.xml',
    ],
    "auto_install": True,
    "installable": True,
}
