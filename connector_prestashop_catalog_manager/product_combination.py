# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import mapping

from openerp.addons.connector_prestashop.unit.exporter import (
    TranslationPrestashopExporter,
    export_record
)
from openerp.addons.connector_prestashop.unit.mapper import \
    TranslationPrestashopExportMapper
from openerp.addons.connector_prestashop.unit.deleter import (
    export_delete_record
)
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.consumer import INVENTORY_FIELDS
from openerp import models, fields
from collections import OrderedDict

EXCLUDE_FIELDS = ['list_price', 'margin']

_logger = logging.getLogger(__name__)


@on_record_create(model_names='prestashop.product.combination')
def prestashop_product_combination_create(session, model_name, record_id,
                                          fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.combination')
def prestashop_product_combination_write(session, model_name,
                                         record_id, fields):
    if session.context.get('connector_no_export'):
        return
    fields = list(set(fields).difference(set(INVENTORY_FIELDS)))

    if fields:
        export_record.delay(session, model_name, record_id,
                            fields, priority=20)


@on_record_write(model_names='product.product')
def product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return

    for field in EXCLUDE_FIELDS:
        fields.pop(field, None)

    model = session.env[model_name]
    record = model.browse(record_id)
    if not record.is_product_variant:
        return

    if 'active' in fields and not fields['active']:
        prestashop_product_combination_unlink(session, record_id)
        return

    if fields:
        # If user modify any variant we delay template export but before
        # check if the template have a queued job
        template = record.mapped('prestashop_bind_ids.product_tmpl_id')
        for binding in template.prestashop_bind_ids:
            # check if there is other queued job
            func = "openerp.addons.connector_prestashop.unit.exporter." \
                   "export_record('prestashop.product.template', %s," \
                   % binding.id
            jobs = session.env['queue.job'].sudo().search(
                [('func_string', 'like', "%s%%" % func),
                 ('state', '!=', 'done')]
            )
            if not jobs:
                export_record.delay(
                    session, 'prestashop.product.template', binding.id,
                    fields,
                )


def prestashop_product_combination_unlink(session, record_id):
    # binding is deactivate when deactive a product variant
    ps_binding_product = session.env['prestashop.product.combination'].search([
        ('active', '=', False),
        ('odoo_id', '=', record_id)
    ])
    for binding in ps_binding_product:
        resource = 'combinations/%s' % (binding.prestashop_id)
        export_delete_record.delay(
            session, 'prestashop.product.combination', binding.backend_id.id,
            binding.prestashop_id, resource)
    ps_binding_product.unlink()


class PrestashopProductCombination(models.Model):
    _inherit = 'prestashop.product.combination'
    minimal_quantity = fields.Integer(
        string='Minimal Quantity',
        default=1,
        help='Minimal Sale quantity',
    )


@prestashop
class ProductCombinationExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.combination'

    def _create(self, record):
        """
        :param record: browse record to create in prestashop
        :return integer: Prestashop record id
        """
        res = super(ProductCombinationExport, self)._create(record)
        return res['prestashop']['combination']['id']

    def _export_images(self):
        if self.erp_record.image_ids:
            image_binder = self.binder_for('prestashop.product.image')
            for image_line in self.erp_record.image_ids:
                image_ext_id = image_binder.to_backend(
                    image_line.id, wrap=True)
                if not image_ext_id:
                    image_ext_id = \
                        self.session.env['prestashop.product.image']\
                            .with_context(connector_no_export=True).create({
                                'backend_id': self.backend_record.id,
                                'odoo_id': image_line.id,
                            }).id
                    image_content = getattr(image_line, "_get_image_from_%s" %
                                            image_line.storage)()
                    export_record(
                        self.session,
                        'prestashop.product.image',
                        image_ext_id,
                        image_content)

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        # TODO add export of category
        attribute_binder = self.binder_for(
            'prestashop.product.combination.option')
        option_binder = self.binder_for(
            'prestashop.product.combination.option.value')
        for value in self.erp_record.attribute_value_ids:
            attribute_ext_id = attribute_binder.to_backend(
                value.attribute_id.id, wrap=True)
            if not attribute_ext_id:
                attribute_ext_id = self.session.env[
                    'prestashop.product.combination.option'].with_context(
                    connector_no_export=True).create({
                        'backend_id': self.backend_record.id,
                        'odoo_id': value.attribute_id.id,
                    })
                export_record(
                    self.session,
                    'prestashop.product.combination.option',
                    attribute_ext_id
                )
            value_ext_id = option_binder.to_backend(value.id, wrap=True)
            if not value_ext_id:
                value_ext_id = self.session.env[
                    'prestashop.product.combination.option.value']\
                    .with_context(connector_no_export=True).create({
                        'backend_id': self.backend_record.id,
                        'odoo_id': value.val_id.id,
                        'id_attribute_group': attribute_ext_id
                    })
                export_record(
                    self.session,
                    'prestashop.product.combination.option.value',
                    value_ext_id)
        # self._export_images()

    def update_quantities(self):
        self.erp_record.odoo_id.with_context(
            self.session.context).update_prestashop_qty()

    def _after_export(self):
        self.update_quantities()


@prestashop
class ProductCombinationExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.combination'

    direct = [
        ('default_code', 'reference'),
        ('active', 'active'),
        ('ean13', 'ean13'),
        ('minimal_quantity', 'minimal_quantity'),
        ('weight', 'weight'),
    ]

    @mapping
    def combination_default(self, record):
        return {'default_on': str(int(record['default_on']))}

    def get_main_template_id(self, record):
        template_binder = self.binder_for('prestashop.product.template')
        return template_binder.to_backend(record.main_template_id.id)

    @mapping
    def main_template_id(self, record):
        return {'id_product': self.get_main_template_id(record)}

    @mapping
    def _unit_price_impact(self, record):
        tax = record.taxes_id[:1]
        factor_tax = tax.price_include and (1 + tax.amount) or 1.0
        return {'price': str(record.impact_price / factor_tax)}

    @mapping
    def cost_price(self, record):
        return {'wholesale_price': str(record.standard_price)}

    def _get_product_option_value(self, record):
        option_value = []
        option_binder = self.binder_for(
            'prestashop.product.combination.option.value')
        for value in record.attribute_value_ids:
            value_ext_id = option_binder.to_backend(value.id, wrap=True)
            if value_ext_id:
                option_value.append({'id': value_ext_id})
        return option_value

    def _get_combination_image(self, record):
        images = []
        image_binder = self.binder_for('prestashop.product.image')
        for image in record.image_ids:
            image_ext_id = image_binder.to_backend(image.id, wrap=True)
            if image_ext_id:
                images.append({'id': image_ext_id})
        return images

    @mapping
    def associations(self, record):
        associations = OrderedDict([
            ('product_option_values',
                {'product_option_value':
                 self._get_product_option_value(record)}),
            ('images', {'image': self._get_combination_image(record) or False})
        ])
        return {'associations': associations}
