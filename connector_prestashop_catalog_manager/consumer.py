# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp.addons.connector.event import (
    on_record_create,
    on_record_write,
    on_record_unlink,
)
from openerp.addons.connector.connector import Binder
from openerp.addons.connector_prestashop.unit.exporter import export_record
from openerp.addons.connector_prestashop.unit.deleter import (
    export_delete_record
)
from openerp.addons.connector_prestashop.consumer import INVENTORY_FIELDS

import unicodedata
import re

try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None


def get_slug(name):
    if slugify_lib:
        try:
            return slugify_lib.slugify(name)
        except TypeError:
            pass
    uni = unicodedata.normalize('NFKD', name).encode(
        'ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[\W_]', ' ', uni).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


# TODO: attach this to a model to ease override
CATEGORY_EXPORT_FIELDS = [
    'name',
    'parent_id',
    'description',
    'link_rewrite',
    'meta_description',
    'meta_keywords',
    'meta_title',
    'position'
]

EXCLUDE_FIELDS = ['list_price']


@on_record_create(model_names='prestashop.product.category')
def prestashop_product_category_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='product.category')
def product_category_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(CATEGORY_EXPORT_FIELDS):
        model = session.env[model_name]
        record = model.browse(record_id)
        for binding in record.prestashop_bind_ids:
            export_record.delay(
                session, binding._model._name, binding.id, fields=fields,
                priority=20)


@on_record_write(model_names='prestashop.product.category')
def prestashop_product_category_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(CATEGORY_EXPORT_FIELDS):
        export_record.delay(session, model_name, record_id, fields)


@on_record_write(model_names='base_multi_image.image')
def product_image_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.image',
                            binding.id, record.file_db_store,
                            priority=20)


@on_record_unlink(model_names='base_multi_image.image')
def product_image_unlink(session, model_name, record_id):
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.prestashop_bind_ids:
        backend = binding.backend_id
        product = session.env[record.owner_model].browse(record.owner_id)
        if product.exists():
            product_template = product.prestashop_bind_ids.filtered(
                lambda x: x.backend_id == binding.backend_id)
            if not product_template:
                return
            env_product = backend.get_environment(
                'prestashop.product.template',
                session=session,
            )
            binder_product = env_product.get_connector_unit(Binder)
            external_product_id = binder_product.to_backend(
                product_template.id)

            env = backend.get_environment(binding._name, session=session)
            binder = env.get_connector_unit(Binder)
            external_id = binder.to_backend(binding.id)
            resource = 'images/products/%s' % (external_product_id)
            if external_id:
                export_delete_record.delay(
                    session, binding._name, binding.backend_id.id,
                    external_id, resource)


@on_record_create(model_names='prestashop.product.template')
def prestashop_product_template_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.template')
def prestashop_product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    fields = list(set(fields).difference(set(INVENTORY_FIELDS)))
    if fields:
        export_record.delay(
            session, model_name, record_id, fields, priority=20
        )
        # Propagate minimal_quantity from template to variants
        if 'minimal_quantity' in fields:
            ps_template = session.env[model_name].browse(record_id)
            for binding in ps_template.prestashop_bind_ids:
                binding.odoo_id.mapped(
                    'product_variant_ids.prestashop_bind_ids').write({
                        'minimal_quantity': binding.minimal_quantity
                    })


@on_record_write(model_names='product.template')
def product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.prestashop_bind_ids:
        export_record.delay(
            session, 'prestashop.product.template', binding.id, fields,
            priority=20,
        )


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
        export_record.delay(
            session, model_name, record_id, fields, priority=20,
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
        for binding in record.prestashop_bind_ids:
            priority = 20
            if 'default_on' in fields and fields['default_on']:
                # PS has to uncheck actual default combination first
                priority = 99
            export_record.delay(
                session,
                'prestashop.product.combination',
                binding.id,
                fields,
                priority=priority,
            )


@on_record_create(model_names='prestashop.product.combination.option')
def prestashop_product_attribute_created(
        session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_create(model_names='prestashop.product.combination.option.value')
def prestashop_product_atrribute_value_created(
        session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.combination.option')
def prestashop_product_attribute_written(session, model_name, record_id,
                                         fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='prestashop.product.combination.option.value')
def prestashop_attribute_option_written(session, model_name, record_id,
                                        fields=None):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, priority=20)


@on_record_write(model_names='product.attribute.value')
def product_attribute_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session, 'prestashop.product.combination.option',
                            binding.id, fields, priority=20)


@on_record_write(model_names='produc.attribute.value')
def attribute_option_written(session, model_name, record_id, fields=None):
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    for binding in record.prestashop_bind_ids:
        export_record.delay(session,
                            'prestashop.product.combination.option.value',
                            binding.id, fields, priority=20)
