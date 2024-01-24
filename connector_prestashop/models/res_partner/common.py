# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component


class ResPartner(models.Model):
    _inherit = "res.partner"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.res.partner",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )
    prestashop_address_bind_ids = fields.One2many(
        comodel_name="prestashop.address",
        inverse_name="odoo_id",
        string="PrestaShop Address Bindings",
    )


class PrestashopPartnerMixin(models.AbstractModel):
    _name = "prestashop.partner.mixin"
    _description = "Mixin for Partner Bindings"

    group_ids = fields.Many2many(
        comodel_name="prestashop.res.partner.category",
        relation="prestashop_category_partner",
        column1="partner_id",
        column2="category_id",
        string="PrestaShop Groups",
    )
    date_add = fields.Datetime(
        string="Created At (on PrestaShop)",
        readonly=True,
    )
    date_upd = fields.Datetime(
        string="Updated At (on PrestaShop)",
        readonly=True,
    )
    default_category_id = fields.Many2one(
        comodel_name="prestashop.res.partner.category",
        string="PrestaShop default category",
        help="This field is synchronized with the field "
        "'Default customer group' in PrestaShop.",
    )
    company = fields.Char(string="Partner Company")


class PrestashopResPartner(models.Model):
    _name = "prestashop.res.partner"
    _inherit = [
        "prestashop.binding.odoo",
        "prestashop.partner.mixin",
    ]
    _inherits = {"res.partner": "odoo_id"}
    _rec_name = "shop_group_id"
    _description = "Partner prestashop bindings"

    odoo_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
        ondelete="cascade",
    )
    backend_id = fields.Many2one(
        related="shop_group_id.backend_id",
        comodel_name="prestashop.backend",
        string="PrestaShop Backend",
        store=True,
        readonly=True,
    )
    shop_group_id = fields.Many2one(
        comodel_name="prestashop.shop.group",
        string="PrestaShop Shop Group",
        required=True,
        ondelete="restrict",
    )
    shop_id = fields.Many2one(
        comodel_name="prestashop.shop",
        string="PrestaShop Shop",
    )
    newsletter = fields.Boolean(string="Newsletter")
    birthday = fields.Date(string="Birthday")

    def import_customers_since(self, backend_record=None, since_date=None, **kwargs):
        """Prepare the import of partners modified on PrestaShop"""
        filters = None
        if since_date:
            filters = {"date": "1", "filter[date_upd]": ">[%s]" % since_date}
        now_fmt = fields.Datetime.now()
        self.env["prestashop.res.partner.category"].import_batch(
            backend=backend_record, filters=filters, priority=10, **kwargs
        )
        self.env["prestashop.res.partner"].import_batch(
            backend=backend_record, filters=filters, priority=15, **kwargs
        )
        backend_record.import_partners_since = now_fmt
        return True


class PrestashopAddressMixin(models.AbstractModel):
    _name = "prestashop.address.mixin"
    _description = "Mixin for prestashop adress bindings"

    date_add = fields.Datetime(
        string="Created At (on PrestaShop)",
        readonly=True,
    )
    date_upd = fields.Datetime(
        string="Updated At (on PrestaShop)",
        readonly=True,
    )
    company = fields.Char(string="Address Company")


class PrestashopAddress(models.Model):
    _name = "prestashop.address"
    _inherit = [
        "prestashop.binding.odoo",
        "prestashop.address.mixin",
    ]
    _inherits = {"res.partner": "odoo_id"}
    _rec_name = "odoo_id"
    _description = "Addreses prestashop bindings"

    prestashop_partner_id = fields.Many2one(
        comodel_name="prestashop.res.partner",
        string="PrestaShop Partner",
        required=True,
        ondelete="cascade",
    )
    backend_id = fields.Many2one(
        comodel_name="prestashop.backend",
        string="PrestaShop Backend",
        related="prestashop_partner_id.backend_id",
        store=True,
        readonly=True,
    )
    odoo_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
        ondelete="cascade",
    )
    shop_group_id = fields.Many2one(
        comodel_name="prestashop.shop.group",
        string="PrestaShop Shop Group",
        related="prestashop_partner_id.shop_group_id",
        store=True,
        readonly=True,
    )
    vat_number = fields.Char("PrestaShop VAT")
    alias = fields.Char("Prestashop Alias")


class PartnerAdapter(Component):
    _name = "prestashop.res.partner.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.res.partner"
    _prestashop_model = "customers"


class PartnerAddressAdapter(Component):
    _name = "prestashop.address.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.address"
    _prestashop_model = "addresses"
