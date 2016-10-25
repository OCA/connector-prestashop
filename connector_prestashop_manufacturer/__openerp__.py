# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Connector Prestashop Manufacturer',
    'summary': 'Import manufacturers from PrestaShop',
    'version': '8.0.1.0.0',
    'category': 'Connector',
    'website': 'https://odoo-community.org/',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'connector_prestashop',
        'product_manufacturer',
    ],
    'data': [
        'data/connector_prestashop_manufacturer_data.xml',
        'data/cron.xml',
        'views/partner_view.xml',
        'views/prestashop_model_view.xml',
        'views/product_view.xml',
        'views/connector_prestashop_menu.xml',
    ]
}
