[![Build Status](https://travis-ci.org/OCA/connector-prestashop.svg?branch=10.0)](https://travis-ci.org/OCA/connector-prestashop)
[![Coverage Status](https://coveralls.io/repos/OCA/connector-prestashop/badge.png?branch=10.0)](https://coveralls.io/r/OCA/connector-prestashop?branch=10.0)

prestashoperpconnect
====================

A module that allows Odoo to connect to Prestashop.

Requirements
------------

You should install prestapyt (akretion branch) and python-requests :

```bash
pip install -r requirements.txt
```

This module is based on modules in other repositories :
- https://github.com/OCA/connector.git
- https://github.com/OCA/connector-ecommerce.git
- https://github.com/OCA/product-attribute.git
- https://github.com/OCA/e-commerce.git
- https://github.com/OCA/sale-workflow.git
 

Getting started
---------------

- install the module prestashoperpconnect
  - settings -> modules
  - choose your country accounting
- install the module  account_accountant 
- configure the chart of account (it seems that it is not required anymore with ocb branches)
  - in settings -> configuration -> Accounting -> Chart of account
  - set the template for your country
  - apply
- configure the prestashop backend
  - Connectors -> prestashop -> backend click create
  - 1st field is the label of the backend
  - Location is of the form http://server:port
  - password is the api key from prestashop admin
  - save
- import the first data from prestashop
  - click on synchronize metadata
  - click on synchronize base data
- configure the tax groups
  - in Accounting -> Configuration -> Taxes -> Taxes
  - set a tax group for each sale vat
- import customers and products
  - click on 'import in background' in front of 'Import customer groups and customers since"
  - click on 'import in background' in front of 'Import product categories and products'
- once these tasks are done (see it in Connectors -> Queue -> Jobs)
  - click on 'import in background' in front of 'import sale orders'


[//]: # (addons)

Available addons
----------------
addon | version | summary
--- | --- | ---
[connector_prestashop](connector_prestashop/) | 10.0.1.0.1 | PrestaShop-Odoo connector


Unported addons
---------------
addon | version | summary
--- | --- | ---
[connector_prestashop_catalog_manager](connector_prestashop_catalog_manager/) | 9.0.1.0.2 (unported) | Prestashop-Odoo Catalog Manager
[connector_prestashop_customize_example](connector_prestashop_customize_example/) | 8.0.1.0.0 (unported) | Prestashop Connector Customization Example
[connector_prestashop_manufacturer](connector_prestashop_manufacturer/) | 9.0.1.0.0 (unported) | Import manufacturers from PrestaShop

[//]: # (end addons)
