# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class PrestashopProductCategoryListener(Component):
    _name = 'prestashop.product.category.event.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'prestashop.product.category'

    def _get_category_export_fields(self):
        return [
            'name',
            'parent_id',
            'description',
            'link_rewrite',
            'meta_description',
            'meta_keywords',
            'meta_title',
            'position'
        ]


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    @skip_if(lambda self, record, **kwargs: self.need_to_export(record, **kwargs))
    def on_record_create(self, record, fields=None):
        """ Called when a record is created """
        record.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    @skip_if(lambda self, record, **kwargs: self.need_to_export(record, **kwargs))
    def on_record_write(self, record, fields=None):
        """ Called when a record is written """
        fields = list(set(fields).difference(
            set(self._get_category_export_fields())))
        if fields:
            record.with_delay().export_record(fields=fields)


class ProductCategoryListener(Component):
    _name = 'product.category.event.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'product.category'

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    @skip_if(lambda self, record, **kwargs: self.need_to_export(record.prestashop_bind_ids, **kwargs))
    def on_record_write(self, record, fields=None):
        """ Called when a record is written """
        listener = self.component(
            usage='event.listener', model_name='prestashop.product.category')
        fields = list(set(fields).difference(
            set(listener._get_category_export_fields())))
        if fields:
            for binding in record.prestashop_bind_ids:
                binding.with_delay().export_record(fields=fields)
