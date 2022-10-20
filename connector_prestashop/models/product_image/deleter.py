# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from ...unit.deleter import PrestashopDeleter
from ...backend import prestashop


@prestashop
class ProductImageDelete(PrestashopDeleter):
    _model_name = 'prestashop.product.image'

    def delete(self, id):
        """ Delete a record on the external system """
        return self._call('%s.delete' % self._prestashop_model, [int(id)])
