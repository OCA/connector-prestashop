# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Connector Prestashop Manufacturer',
    'summary': 'Import manufacturers from PrestaShop',
    'version': '9.0.1.0.0',
    'category': 'Connector',
    'website': 'https://odoo-community.org/',
    'author': 'Tecnativa, '
              'Camptocamp SA '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'connector_prestashop',
        'connector_prestashop_catalog_manager',
        'product_manufacturer',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/connector_prestashop_manufacturer_data.xml',
        'data/cron.xml',
        'views/partner_view.xml',
        'views/prestashop_model_view.xml',
        'views/product_view.xml',
        'views/connector_prestashop_menu.xml',
    ]
}
