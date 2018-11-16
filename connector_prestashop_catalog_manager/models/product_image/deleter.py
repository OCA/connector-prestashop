# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductImageDeleter(Component):
    _name = 'prestashop.product.image.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = 'prestashop.product.image'

    def _run(self):
        assert self.binding_id
        assert self.binding

        backend = self.binding.backend_id
        if self.prestashop_id:
            with backend.work_on('prestashop.product.image') as work:
                exporter = work.component(usage='record.exporter')
                map_record = exporter.mapper.map_record(self.binding)
                record = map_record.values()

                res = self.backend_adapter.delete(self.prestashop_id, record)
                return res
        else:
            return _('Nothing to delete.')
