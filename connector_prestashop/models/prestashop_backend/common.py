# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, exceptions, fields, models

from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.component.core import Component

from ...components.backend_adapter import api_handle_errors

_logger = logging.getLogger(__name__)


class PrestashopBackend(models.Model):
    _name = "prestashop.backend"
    _description = "PrestaShop Backend Configuration"
    _inherit = "connector.backend"

    _versions = {
        "1.5": "prestashop.version.key",
        "1.6.0.9": "prestashop.version.key.1.6.0.9",
        "1.6.0.11": "prestashop.version.key.1.6.0.9",
        "1.6.1.2": "prestashop.version.key.1.6.1.2",
        "1.6.1.6": "prestashop.version.key.1.6.1.6",
        "1.6.1.9": "prestashop.version.key.1.6.1.9",
        "1.7.5.0": "prestashop.version.key.1.7.5.0",
        "1.7.x.0": "prestashop.version.key.1.7.x.0",
    }

    @api.model
    def select_versions(self):
        """Available versions

        Can be inherited to add custom versions.
        """
        return [
            ("1.5", "< 1.6.0.9"),
            ("1.6.0.9", "1.6.0.9 - 1.6.0.10"),
            ("1.6.0.11", ">= 1.6.0.11 - <1.6.1.2"),
            ("1.6.1.2", "=1.6.1.2"),
            ("1.6.1.6", ">=1.6.1.6 - <1.6.1.9"),
            ("1.6.1.9", "=1.6.1.9"),
            ("1.7.x.0", ">=1.7.x.0 - <1.7.5.0"),
            ("1.7.5.0", "=1.7.5.0"),
        ]

    @api.model
    def _select_state(self):
        """Available States for this Backend"""
        return [
            ("draft", "Draft"),
            ("checked", "Checked"),
            ("production", "In Production"),
        ]

    name = fields.Char(string="Name", required=True)
    version = fields.Selection(
        selection="select_versions",
        string="Version",
        required=True,
    )
    location = fields.Char("Location")
    webservice_key = fields.Char(
        string="Webservice key",
        help="You have to put it in 'username' of the PrestaShop "
        "Webservice api path invite",
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
        required=True,
        help="Warehouse used to compute the stock quantities.",
    )
    stock_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Stock Location",
        help="Location used to import stock quantities.",
    )
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Pricelist",
        required=True,
        default=lambda self: self._default_pricelist_id(),
        help="Pricelist used in sales orders",
    )
    sale_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team",
        help="Sales Team assigned to the imported sales orders.",
    )

    refund_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Refund Journal",
    )

    taxes_included = fields.Boolean("Use tax included prices")
    import_partners_since = fields.Datetime("Import partners since")
    import_orders_since = fields.Datetime("Import Orders since")
    import_payment_mode_since = fields.Datetime("Import Payment Modes since")
    import_products_since = fields.Datetime("Import Products since")
    import_refunds_since = fields.Datetime("Import Refunds since")
    import_suppliers_since = fields.Datetime("Import Suppliers since")
    language_ids = fields.One2many(
        comodel_name="prestashop.res.lang",
        inverse_name="backend_id",
        string="Languages",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        index=True,
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "prestashop.backend"
        ),
        string="Company",
    )
    discount_product_id = fields.Many2one(
        comodel_name="product.product",
        index=True,
        required=True,
        string="Discount Product",
    )
    shipping_product_id = fields.Many2one(
        comodel_name="product.product",
        index=True,
        required=True,
        string="Shipping Product",
    )
    importable_order_state_ids = fields.Many2many(
        comodel_name="sale.order.state",
        string="Importable sale order states",
        help="If valued only orders matching these states will be imported.",
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(selection="_select_state", string="State", default="draft")

    verbose = fields.Boolean(help="Output requests details in the logs")
    debug = fields.Boolean(help="Activate PrestaShop's webservice debug mode")

    matching_product_template = fields.Boolean(string="Match product template")

    matching_product_ch = fields.Selection(
        [("reference", "Reference"), ("barcode", "Barcode")],
        string="Matching Field for product",
    )

    matching_customer = fields.Boolean(
        string="Matching Customer",
        help="The selected fields will be matched to the ref field of the "
        "partner. Please adapt your datas consequently.",
    )
    # matching_customer_ch = fields.Many2one(
    #     comodel_name='prestashop.partner.field', string="Matched field",
    #     help="Field that will be matched.")
    tz = fields.Selection(
        _tz_get,
        "Timezone",
        help="The timezone of the backend. Used to synchronize the sale order date.",
    )
    product_qty_field = fields.Selection(
        selection=[
            ("qty_available_not_res", "Immediately usable qty"),
            ("qty_available", "Qty available"),
        ],
        string="Product qty",
        help="Select how you want to calculate the qty to push to PS. ",
        default="qty_available",
        required=True,
    )
    default_language = fields.Many2one(
        comodel_name="res.lang",
        default=lambda self: self.env["res.lang"]
        .search([("code", "=", self.env.user.lang)])[0]
        .id,
    )

    @api.constrains("product_qty_field")
    def check_product_qty_field_dependencies_installed(self):
        for backend in self:
            # we only support stock_available_unreserved module for now.
            # In order to support stock_available_immediately or
            # virtual_available for example, we would need to recompute
            # the prestashop qty at stock move level, it can't work to
            # recompute it only at quant level, like it is done today
            if backend.product_qty_field == "qty_available_not_res":
                module = (
                    self.env["ir.module.module"]
                    .sudo()
                    .search([("name", "=", "stock_available_unreserved")], limit=1)
                )
                if not module or module.state != "installed":
                    raise exceptions.UserError(
                        _(
                            "In order to choose this option, you have to "
                            "install the module stock_available_unreserved."
                        )
                    )

    @api.onchange("matching_customer")
    def change_matching_customer(self):
        # Update the field list so that if you API change you could find the
        # new fields to map
        if self._origin.id:
            self.fill_matched_fields(self._origin.id)

    def fill_matched_fields(self, backend_id):
        self.ensure_one()

        # options = {'limit': 1, 'display': 'full'}
        # TODO : Unse new adapter pattern to get a simple partner json

    #         prestashop = PrestaShopLocation(
    #                         self.location.encode(),
    #                         self.webservice_key,
    #                     )
    #
    #         client = PrestaShopWebServiceDict(
    #                     prestashop.api_url,
    #                     prestashop.webservice_key)
    #
    #         customer = client.get('customers', options=options)
    #         tab=customer['customers']['customer'].keys()
    #         for key in tab:
    #             key_present = self.env['prestashop.partner.field'].search(
    #                     [('value', '=', key), ('backend_id', '=', backend_id)])
    #
    #             if len(key_present) == 0 :
    #                 self.env['prestashop.partner.field'].create({
    #                     'name' : key,
    #                     'value' : key,
    #                     'backend_id': backend_id
    #                 })

    @api.model
    def _default_pricelist_id(self):
        return self.env["product.pricelist"].search([], limit=1)

    def button_reset_to_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    def synchronize_metadata(self):
        for backend in self:
            for model_name in ["prestashop.shop.group", "prestashop.shop"]:
                # import directly, do not delay because this
                # is a fast operation, a direct return is fine
                # and it is simpler to import them sequentially
                self.env[model_name].import_batch(backend)
        return True

    def synchronize_basedata(self):
        for backend in self:
            for model_name in [
                "prestashop.res.lang",
                "prestashop.res.country",
                "prestashop.res.currency",
                "prestashop.account.tax",
            ]:
                with backend.work_on(model_name) as work:
                    importer = work.component(usage="auto.matching.importer")
                    importer.run()
            self.env["prestashop.account.tax.group"].import_batch(backend)
            self.env["prestashop.sale.order.state"].import_batch(backend)
        return True

    def _check_connection(self):
        self.ensure_one()
        with self.work_on("prestashop.backend") as work:
            component = work.component_by_name(name="prestashop.adapter.test")
            with api_handle_errors("Connection failed"):
                component.head()

    def button_check_connection(self):
        self._check_connection()
        # raise exceptions.UserError(_('Connection successful'))
        self.write({"state": "checked"})

    def import_customers_since(self):
        for backend_record in self:
            since_date = backend_record.import_partners_since
            self.env["prestashop.res.partner"].with_delay().import_customers_since(
                backend_record=backend_record, since_date=since_date
            )
        return True

    def import_products(self):
        for backend_record in self:
            since_date = backend_record.import_products_since
            self.env["prestashop.product.template"].with_delay().import_products(
                backend_record, since_date
            )
        return True

    def import_carriers(self):
        for backend_record in self:
            self.env["prestashop.delivery.carrier"].with_delay().import_batch(
                backend_record,
            )
        return True

    def update_product_stock_qty(self):
        for backend_record in self:
            backend_record.env[
                "prestashop.product.template"
            ].with_delay().export_product_quantities(backend=backend_record)
            backend_record.env[
                "prestashop.product.combination"
            ].with_delay().export_product_quantities(backend=backend_record)
        return True

    def import_stock_qty(self):
        for backend_record in self:
            backend_record.env[
                "prestashop.product.template"
            ].with_delay().import_inventory(backend_record)

    def import_sale_orders(self):
        for backend_record in self:
            since_date = backend_record.import_orders_since
            backend_record.env[
                "prestashop.sale.order"
            ].with_delay().import_orders_since(backend_record, since_date)
        return True

    def import_payment_modes(self):
        now_fmt = fields.Datetime.now()
        for backend_record in self:
            since_date = backend_record.import_payment_mode_since
            filters = {}
            if since_date:
                filters = {"date": "1", "filter[date_upd]": ">[%s]" % (since_date)}
            with backend_record.work_on("account.payment.mode") as work:
                importer = work.component(usage="batch.importer")
                importer.run(filters=filters)
            backend_record.import_payment_mode_since = now_fmt
        return True

    def import_refunds(self):
        for backend_record in self:
            since_date = backend_record.import_refunds_since
            backend_record.env["prestashop.refund"].import_refunds(
                backend_record, since_date
            )
        return True

    def import_suppliers(self):
        for backend_record in self:
            since_date = backend_record.import_suppliers_since
            backend_record.env["prestashop.supplier"].import_suppliers(
                backend_record, since_date
            )
        return True

    def get_version_ps_key(self, key):
        self.ensure_one()
        with self.work_on("_prestashop.version.key") as work:
            keys = work.component(usage=self._versions[self.version])
            return keys.get_key(key)

    @api.model
    def _scheduler_update_product_stock_qty(self, domain=None):
        self.search(domain or []).update_product_stock_qty()

    @api.model
    def _scheduler_import_refunds(self, domain=None):
        self.search(domain or []).import_refunds()

    @api.model
    def _scheduler_import_sale_orders(self, domain=None):
        self.search(domain or []).import_sale_orders()

    @api.model
    def _scheduler_import_customers(self, domain=None):
        self.search(domain or []).import_customers_since()

    @api.model
    def _scheduler_import_products(self, domain=None):
        self.search(domain or []).import_products()

    @api.model
    def _scheduler_import_carriers(self, domain=None):
        self.search(domain or []).import_carriers()

    @api.model
    def _scheduler_import_payment_methods(self, domain=None):
        backends = self.search(domain or [])
        backends.import_payment_modes()
        backends.import_refunds()

    @api.model
    def _scheduler_import_suppliers(self, domain=None):
        self.search(domain or []).import_suppliers()

    def _get_locations_for_stock_quantities(self):
        root_location = self.stock_location_id or self.warehouse_id.lot_stock_id
        locations = self.env["stock.location"].search(
            [
                ("id", "child_of", root_location.id),
                ("prestashop_synchronized", "=", True),
                ("usage", "=", "internal"),
            ]
        )
        # if we choosed a location but none where flagged
        # 'prestashop_synchronized', consider we want all of them in the tree
        if not locations:
            locations = self.env["stock.location"].search(
                [
                    ("id", "child_of", root_location.id),
                    ("usage", "=", "internal"),
                ]
            )
        if not locations:
            # we must not pass an empty location or we would have the
            # stock for every warehouse, which is the last thing we
            # expect
            raise exceptions.UserError(
                _("No internal location found to compute the product quantity.")
            )
        return locations


class NoModelAdapter(Component):
    """Used to test the connection"""

    _name = "prestashop.adapter.test"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.backend"
    _prestashop_model = ""
