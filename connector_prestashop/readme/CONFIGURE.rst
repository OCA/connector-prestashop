To configure this module, you need to set several things in both PrestaShop
and Odoo:

Steps in PrestaShop
===================

#. Go to the control panel (usually at <url>/adminps).
#. Login into the system.
#. Go to *Advanced Parameters > Web service*
#. Add a new entry.
#. Generate a new API key that will be needed later.
#. Grant all the needed access according your security policy.

Steps in Odoo
=============

#. Go to *Connectors > PrestaShop > Backends*.
#. Create a new record for registering a PrestaShop backend. You will bind
   this backend to an specific company and warehouse.
#. Define the main URL of the PrestaShop web, and the webservice key you
   got in PrestaShop.
#. Define other parameters like the discount and shipping products, or if the
   taxes are included in the price.
#. Click on "Synchronize Metadata" button. This will bring the basic shop
   information that you can find on *Websites* and *Stores* menus.
#. Click on "Synchronize Base Data" button. This will import carriers,
   languages, tax groups and the rest of base data that are needed for the
   proper work.
#. Go to *Accounting > Configuration > Taxes > Tax Groups*, and include
   for each of the tax definition imported from PrestaShop, the corresponding
   taxes in Odoo.
#. Activate the job runner, checking the connector documentation for setting
   the server correctly for using it in
   http://odoo-connector.com/guides/jobrunner.html
#. Alternatively, if you are not able to activate it, you can enable the
   scheduled job called "Enqueue Jobs".
#. Activate the scheduled jobs for importing the records you want:

  * PrestaShop - Export Stock Quantities
  * PrestaShop - Import Carriers
  * PrestaShop - Import Customers and Groups
  * PrestaShop - Import Products and Categories
  * PrestaShop - Import Sales Orders
  * PrestaShop - Import suppliers
  * PrestaShop - Payment methods
