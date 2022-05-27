# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Connector  Choose Odoo as owner of the taxes',
    'summary': 'Odoo owner of the taxes computation',
    'version': '14.0.1.0.1',
    'category': 'Connector',
    'website': 'https://odoo-community.org/',
    'author': 'Tecnativa, '
              'Camptocamp SA, '
              'Mind And Go, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'connector_prestashop',
    ],
    'data': [
        'views/prestashop_backend_view.xml',
    ]
}
