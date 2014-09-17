[![Build Status](https://travis-ci.org/OCA/connector-prestashop.svg?branch=7.0)](https://travis-ci.org/OCA/connector-prestashop)
[![Coverage Status](https://coveralls.io/repos/OCA/connector-prestashop/badge.png?branch=7.0)](https://coveralls.io/r/OCA/connector-prestashop?branch=7.0)

prestashoperpconnect
====================

A module that permits OpenERP to connect to Prestashop.

Requirements
------------

You should install python libraries and other OCA repositories.
Please refer to the travis.yml file.


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

