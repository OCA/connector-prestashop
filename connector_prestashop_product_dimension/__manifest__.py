# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Connector Prestashop Product Dimension",
    "summary": "Import product dimensions from PrestaShop",
    "version": "10.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Connector",
    "website": "https://github.com/OCA/connector-prestashop",
    "author": "PlanetaTIC, Odoo Community Association (OCA)",
    "maintainers": ["PlanetaTIC"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "connector_prestashop",
        "product_dimension",
    ],
    "auto_install": True,
}
