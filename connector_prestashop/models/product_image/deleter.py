# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ProductImageDelete(Component):
    _name = "prestashop.product.image.deleter"
    _inherit = "prestashop.deleter"
    _apply_on = "prestashop.product.image"

    _model_name = "prestashop.product.image"

    def delete(self, id_):
        """ Delete a record on the external system """
        return self._call("%s.delete" % self._prestashop_model, [int(id_)])
