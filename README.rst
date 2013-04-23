prestashoperpconnect
====================

A module that permits OpenERP to connect to Prestashop.

Requirements
------------

.. code-block:: shell

   pip install -r requirements.txt

Getting started
---------------

- install the module prestashoperpconnect
  - settings -> modules
  - choose your country accounting
- install the module  account_accountant 
- configure the chart of account
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
- import groups
  - click on 'import in background' in front of 'import all customers group"
  - click on 'import in background' in front of 'import all product categories'
- once these tasks are done (see it in Connectors -> Queue -> Jobs)
  - click on 'import in background' in front of 'import partners since'
  - click on 'import in background' in front of 'import all products'
- once these tasks are done (see it in Connectors -> Queue -> Jobs)
  - click on 'import in background' in front of 'import sale orders'

