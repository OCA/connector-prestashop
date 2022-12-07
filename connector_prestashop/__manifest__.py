# Copyright 2011-2013 Camptocamp
# Copyright 2011-2013 Akretion
# Copyright 2015 AvanzOSC
# Copyright 2015-2016 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PrestaShop-Odoo connector",
    "version": "14.0.2.0.2",
    "license": "AGPL-3",
    "depends": [
        "account",
        "base_vat",  # for vat validation on partner address
        "product",
        "product_multi_category",  # oca/product-attribute
        "product_multi_image",  # oca/product-attribute
        "connector_ecommerce",  # oca/connector-ecommerce
        "purchase",
        "onchange_helper",
    ],
    "external_dependencies": {
        "python": [
            "html2text",
            "prestapyt",
            # tests dependencies
            "freezegun",
            "vcrpy",
            "bs4",
        ],
    },
    "author": "Akretion,"
    "Camptocamp,"
    "AvanzOSC,"
    "Tecnativa,"
    "Mind And Go,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Connector",
    "demo": ["demo/backend.xml"],
    "data": [
        "security/ir.model.access.csv",
        "security/prestashop_security.xml",
        "data/queue_job_data.xml",
        "data/cron.xml",
        "data/product_decimal_precision.xml",
        "data/ecommerce_data.xml",
        "views/prestashop_backend_view.xml",
        "views/product_view.xml",
        "views/product_category_view.xml",
        "views/image_view.xml",
        "views/delivery_view.xml",
        "views/connector_prestashop_menu.xml",
        "views/partner_view.xml",
        "views/sale_view.xml",
        "views/account_view.xml",
        "views/stock_view.xml",
        "views/queue_job_views.xml",
    ],
    "installable": True,
    "application": True,
}
