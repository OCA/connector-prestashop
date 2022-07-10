# Copyright 2011-2013 Camptocamp
# Copyright 2011-2013 Akretion
# Copyright 2015 AvanzOSC
# Copyright 2015-2016 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Prestashop-Odoo Catalog Manager",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "connector_prestashop",
        "product_categ_image",
        "product_multi_image",
        "product_brand",
    ],
    "author": "Akretion,"
    "AvanzOSC,"
    "Tecnativa,"
    "Camptocamp SA,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Connector",
    "data": [
        "security/ir.model.access.csv",
        "wizards/export_category_views.xml",
        "wizards/export_multiple_products_views.xml",
        "wizards/sync_products_views.xml",
        "wizards/active_deactive_products_views.xml",
        "wizards/export_brand_views.xml",
        "views/prestashop_product_combination_option_views.xml",
        "views/prestashop_product_template_views.xml",
        "views/product_attribute_views.xml",
        "views/product_attribute_views.xml",
        "views/base_multi_image_views.xml",
        "views/prestashop_product_category_views.xml",
        "views/product_brand_views.xml",
    ],
    "installable": True,
}
