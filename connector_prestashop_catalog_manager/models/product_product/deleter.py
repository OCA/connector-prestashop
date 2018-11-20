# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductCombinationDeleter(Component):
    _name = 'prestashop.product.combination.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = 'prestashop.product.combination'

    def _run(self):
        assert self.binding_id
        assert self.binding

        backend = self.binding.backend_id
        if self.prestashop_id:
            with backend.work_on('prestashop.product.combination') as work:
                exporter = work.component(usage='record.exporter')
                map_record = exporter.mapper.map_record(self.binding)
                record = map_record.values()

                resource = self.backend_adapter._prestashop_model +\
                    '/%s' % self.prestashop_id
                res = self.backend_adapter.delete(resource, self.prestashop_id)
                return res
        else:
            return _('Nothing to delete.')
