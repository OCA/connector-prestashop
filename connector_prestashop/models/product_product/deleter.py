# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from ...components.deleter import PrestashopDeleter


class ProductCombinationDelete(PrestashopDeleter):
    _model_name = "prestashop.product.combination"

    def delete(self, id_):
        """ Delete a record on the external system """
        return self._call("%s.delete" % self._prestashop_model, [int(id_)])
