# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component


class MailMessage(models.Model):
    _inherit = "mail.message"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.mail.message",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )


class PrestashopMailMessage(models.Model):
    _name = "prestashop.mail.message"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"mail.message": "odoo_id"}

    odoo_id = fields.Many2one(
        comodel_name="mail.message",
        required=True,
        ondelete="cascade",
        string="Message",
        oldname="openerp_id",
    )


class MailMessageAdapter(Component):
    _name = "prestashop.mail.message.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.mail.message"
    # pylint: disable=method-required-super

    @property
    def _prestashop_model(self):
        return self.backend_record.get_version_ps_key("messages")

    def read(self, id_, attributes=None):
        """Merge message and thread datas

        :rtype: dict
        """
        api = self.client
        res = api.get(self._prestashop_model, id_, options=attributes)
        first_key = list(res)[0]
        message_data = res[first_key]
        thread_data = api.get(
            "customer_threads", message_data["id_customer_thread"], options=attributes
        )
        first_key = list(thread_data)[0]
        del thread_data[first_key]["id"]
        del thread_data[first_key]["date_add"]
        message_data.update(thread_data[first_key])
        return message_data
