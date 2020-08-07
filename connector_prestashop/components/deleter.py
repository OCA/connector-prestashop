# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools.translate import _

from odoo.addons.component.core import AbstractComponent


class PrestashopDeleter(AbstractComponent):
    """ Base deleter for PrestaShop """

    _name = "prestashop.deleter"
    _inherit = "base.deleter"
    _usage = "record.exporter.deleter"

    def run(self, external_id, attributes=None):
        """Run the synchronization, delete the record on PrestaShop

        :param external_id: identifier of the record to delete
        """
        resource = self.backend_adapter._prestashop_model
        self.backend_adapter.delete(resource, external_id, attributes)
        return _("Record %s deleted on PrestaShop on resource %s") % (
            external_id,
            resource,
        )
