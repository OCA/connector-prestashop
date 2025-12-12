To configure this module, you need to set several things in both
PrestaShop and Odoo:

## Steps in PrestaShop

1.  Go to the control panel (usually at \<url\>/adminps).
2.  Login into the system.
3.  Go to *Advanced Parameters \> Web service*
4.  Add a new entry.
5.  Generate a new API key that will be needed later.
6.  Grant all the needed access according your security policy.

## Steps in Odoo

1.  Go to *Connectors \> PrestaShop \> Backends*.
2.  Create a new record for registering a PrestaShop backend. You will
    bind this backend to an specific company and warehouse.
3.  Define the main URL of the PrestaShop web, and the webservice key
    you got in PrestaShop.
4.  Define other parameters like the discount and shipping products, or
    if the taxes are included in the price.
5.  Click on "Synchronize Metadata" button. This will bring the basic
    shop information that you can find on *Websites* and *Stores* menus.
6.  Click on "Synchronize Base Data" button. This will import carriers,
    languages, tax groups and the rest of base data that are needed for
    the proper work.
7.  Go to *Invoicing \> Configuration \> Accounting \> Tax Groups*, and
    include for each of the tax definition imported from PrestaShop, the
    corresponding taxes in Odoo.
8.  Activate the job runner, checking the connector documentation for
    setting the server correctly for using it in
    <http://odoo-connector.com/guides/jobrunner.html>
9.  Alternatively, if you are not able to activate it, you can enable
    the scheduled job called "Enqueue Jobs".
10. Activate the scheduled jobs for importing the records you want:

> - PrestaShop - Export Stock Quantities
> - PrestaShop - Import Carriers
> - PrestaShop - Import Customers and Groups
> - PrestaShop - Import Products and Categories
> - PrestaShop - Import Sales Orders
> - PrestaShop - Import suppliers
> - PrestaShop - Payment methods
