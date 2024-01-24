This module connects Odoo and PrestaShop.

PrestaShop (http://www.prestashop.com/) is a popular e-commerce platform
written in PHP/MySQL and published under the Open Software licence v3.0.

This module allows the synchronization of the following objects from PrestaShop
to Odoo:

* Websites
* Stores and languages
* Carriers
* Product categories
* Products
* Combinations of products
* Partner categories
* Customers

Once these objects are synchronised, it will allow the import of sales orders,
together with the related customers.

As an extra feature, you can also export the stock quantities back to
PrestaShop.

If you want to export from Odoo to PrestaShop changes made on the products,
product categories or product images, you need to install
*connector_prestashop_catalog_manager* module in this same repository.

This connector supports PrestaShop version up to 1.6.11. Maybe later versions
are also supported, but they haven't been tested. It uses the webservices of
PrestaShop.
