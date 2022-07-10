# Copyright 2011-2013 Camptocamp
# Copyright 2011-2013 Akretion
# Copyright 2015 AvanzOSC
# Copyright 2015-2016 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PrestaShop-Odoo connector",
    "version": "13.0.1.0.0",
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
        "python": ["html2text", "prestapyt", "freezegun", "vcrpy", "bs4"],
    },
    "author": "Akretion,"
    "Camptocamp,"
    "AvanzOSC,"
    "Tecnativa,"
    "Mind And Go,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Connector",
    "maintainers": ["cubells"],
    "data": [
        "security/ir.model.access.csv",
        "security/prestashop_security.xml",
        "data/queue_job_data.xml",
        "data/cron.xml",
        "data/product_decimal_precision.xml",
        "data/ecommerce_data.xml",
        "views/prestashop_backend_views.xml",
        "views/prestashop_shop_group_views.xml",
        "views/prestashop_shop_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
        "views/prestashop_product_combination_views.xml",
        "views/prestashop_product_template_views.xml",
        "views/prestashop_product_category_views.xml",
        "views/product_category_views.xml",
        "views/prestashop_product_image_views.xml",
        "views/prestashop_delivery_views.xml",
        "views/connector_prestashop_menu.xml",
        "views/res_partner_views.xml",
        "views/prestashop_res_partner_views.xml",
        "views/prestashop_address_views.xml",
        "views/res_partner_category_views.xml",
        "views/prestashop_res_partner_category_views.xml",
        "views/sale_order_state_views.xml",
        "views/prestashop_sale_order_state_views.xml",
        "views/prestashop_sale_order_views.xml",
        "views/sale_order_views.xml",
        "views/stock_warehouse_views.xml",
        "views/account_tax_group_views.xml",
        "views/prestashop_account_tax_group_views.xml",
        "views/stock_location_views.xml",
        "views/queue_job_views.xml",
        "demo/backend.xml",
    ],
    "installable": True,
    "application": True,
}
