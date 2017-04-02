# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Exporter

from ...unit.backend_adapter import GenericAdapter
from ...backend import prestashop


@prestashop
class ProductInventoryExporter(Exporter):
    _model_name = ['prestashop.product.template']

    def get_filter(self, template):
        binder = self.binder_for()
        prestashop_id = binder.to_backend(template.id)
        return {
            'filter[id_product]': prestashop_id,
            'filter[id_product_attribute]': 0
        }

    def run(self, binding_id, fields, **kwargs):
        """ Export the product inventory to PrestaShop """
        template = self.model.browse(binding_id)
        adapter = self.unit_for(GenericAdapter, '_import_stock_available')
        filter = self.get_filter(template)
        adapter.export_quantity(filter, int(template.quantity))


@job(default_channel='root.prestashop')
def export_inventory(session, model_name, record_id, fields=None, **kwargs):
    """ Export the inventory configuration and quantity of a product. """
    binding = session.env[model_name].browse(record_id)
    backend = binding.backend_id
    env = backend.get_environment(model_name, session=session)
    inventory_exporter = env.get_connector_unit(ProductInventoryExporter)
    return inventory_exporter.run(record_id, fields, **kwargs)


@job(default_channel='root.prestashop')
def export_product_quantities(session, ids):
    for model in ['template', 'combination']:
        model_obj = session.env['prestashop.product.' + model]
        model_obj.search([
            ('backend_id', 'in', [ids]),
        ]).recompute_prestashop_qty()
