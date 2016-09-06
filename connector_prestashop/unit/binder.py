# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.connector import Binder
from ..backend import prestashop


@prestashop
class PrestashopBinder(Binder):
    """ Generic Binder for Prestshop """

    _external_field = 'prestashop_id'

    _model_name = [
        'prestashop.shop.group',
        'prestashop.shop',
        'prestashop.res.partner',
        'prestashop.address',
        'prestashop.res.partner.category',
        'prestashop.res.lang',
        'prestashop.res.country',
        'prestashop.res.currency',
        'prestashop.account.tax',
        'prestashop.account.tax.group',
        'prestashop.product.category',
        'prestashop.product.image',
        'prestashop.product.product',
        'prestashop.product.template',
        'prestashop.product.combination',
        'prestashop.product.combination.option',
        'prestashop.product.combination.option.value',
        'prestashop.sale.order',
        'prestashop.sale.order.state',
        'prestashop.delivery.carrier',
        'prestashop.refund',
        'prestashop.supplier',
        'prestashop.product.supplierinfo',
        'prestashop.mail.message',
        'prestashop.groups.pricelist',
        # 'prestashop.product.specificprice',
    ]

    # method overrided here until https://github.com/OCA/connector/pull/207
    # is merged
    def to_openerp(self, external_id, unwrap=False):
        """ Give the OpenERP ID for an external ID

        :param external_id: external ID for which we want
                            the OpenERP ID
        :param unwrap: if True, returns the normal record
                       else return the binding record
        :return: a recordset, depending on the value of unwrap,
                 or an empty recordset if the external_id is not mapped
        :rtype: recordset
        """
        bindings = self.model.with_context(active_test=False).search(
            [(self._external_field, '=', str(external_id)),
             (self._backend_field, '=', self.backend_record.id)]
        )
        if not bindings:
            if unwrap:
                return getattr(self.model.browse(), self._openerp_field)
            return self.model.browse()
        bindings.ensure_one()
        if unwrap:
            bindings = getattr(bindings, self._openerp_field)
        return bindings
