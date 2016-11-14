# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Connector Prestashop Product Feature',
    'summary': 'Import product features from PrestaShop',
    'version': '9.0.1.0.0',
    'category': 'Connector',
    'website': 'https://odoo-community.org/',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'connector_prestashop',
        'product_custom_info',
    ],
    'data': [
        'data/custom.info.template.csv',
        'data/cron.xml',
        'views/prestashop_model_view.xml',
    ]
}
