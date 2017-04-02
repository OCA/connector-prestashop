# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from openerp import models

from openerp.addons.connector.queue.job import job

from ...connector import get_environment
from ...backend import prestashop
from ...unit.importer import (
    DelayedBatchImporter,
    PrestashopImporter,
    import_batch,
    import_record,
    TranslatableRecordImporter
)
from ..product_image.importer import (
    set_product_image_variant,
    import_product_image
)
from openerp.addons.connector.unit.mapper import ImportMapper, mapping
from ...unit.mapper import backend_to_m2o
from ...unit.backend_adapter import GenericAdapter
from openerp.addons.product.product import check_ean
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug('Can not `from prestapyt import PrestaShopWebServiceError`.')

try:
    import html2text
except ImportError:
    _logger.debug('Can not `import html2text`.')


@prestashop
class TemplateMapper(ImportMapper):
    _model_name = 'prestashop.product.template'

    direct = [
        ('description', 'description_html'),
        ('description_short', 'description_short_html'),
        ('weight', 'weight'),
        ('wholesale_price', 'standard_price'),
        (backend_to_m2o('id_shop_default'), 'default_shop_id'),
        ('link_rewrite', 'link_rewrite'),
        ('reference', 'reference'),
        ('available_for_order', 'available_for_order'),
        ('on_sale', 'on_sale'),
    ]

    def get_sale_price(self, record, tax):
        price_adapter = self.unit_for(
            GenericAdapter, 'prestashop.product.combination')
        combination = price_adapter.read(
            record['id_default_combination']['value'])
        impact_price = float(combination['price'] or '0.0')
        price = float(record['price'] or '0.0')
        if tax:
            tax = tax[:1]
            return (price / (1 + tax.amount) - impact_price) * (1 + tax.amount)
        price = float(record['price'] or '0.0') - impact_price
        return price

    @mapping
    def list_price(self, record):
        price = 0.0
        tax = self._get_tax_ids(record)
        associations = record.get('associations', {})
        combinations = associations.get('combinations', {}).get(
            'combinations', [])
        if not isinstance(combinations, list):
            combinations = [combinations]
        if combinations:
            price = self.get_sale_price(record, tax)
        else:
            if record['price'] != '':
                price = float(record['price'])
        return {'list_price': price}

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']}
        return {'name': 'noname'}

    @mapping
    def date_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date_add': datetime.now()}
        return {'date_add': record['date_add']}

    @mapping
    def date_upd(self, record):
        if record['date_upd'] == '0000-00-00 00:00:00':
            return {'date_upd': datetime.now()}
        return {'date_upd': record['date_upd']}

    def has_combinations(self, record):
        combinations = record.get('associations', {}).get(
            'combinations', {}).get('combinations', [])
        return len(combinations) != 0

    def _template_code_exists(self, code):
        model = self.session.env['product.template']
        template_ids = model.search([
            ('default_code', '=', code),
            ('company_id', '=', self.backend_record.company_id.id),
        ], limit=1)
        return len(template_ids) > 0

    @mapping
    def default_code(self, record):
        if self.has_combinations(record):
            return {}
        code = record.get('reference')
        if not code:
            code = "backend_%d_product_%s" % (
                self.backend_record.id, record['id']
            )
        if not self._template_code_exists(code):
            return {'default_code': code}
        i = 1
        current_code = '%s_%d' % (code, i)
        while self._template_code_exists(current_code):
            i += 1
            current_code = '%s_%d' % (code, i)
        return {'default_code': current_code}

    def clear_html_field(self, content):
        html = html2text.HTML2Text()
        html.ignore_images = True
        html.ignore_links = True
        return html.handle(content)

    @mapping
    def description(self, record):
        return {
            'description': self.clear_html_field(
                record.get('description_short', '')),
        }

    @mapping
    def active(self, record):
        return {'always_available': bool(int(record['active']))}

    @mapping
    def sale_ok(self, record):
        # if this product has combinations, we do not want to sell this
        # product, but its combinations (so sale_ok = False in that case).
        return {'sale_ok': True}

    @mapping
    def purchase_ok(self, record):
        return {'purchase_ok': True}

    @mapping
    def categ_id(self, record):
        if not int(record['id_category_default']):
            return
        category = self.binder_for(
            'prestashop.product.category').to_odoo(
                record['id_category_default'], unwrap=True)

        if category:
            return {'categ_id': category.id}

        categories = record['associations'].get('categories', {}).get(
            self.backend_record.get_version_ps_key('category'), [])
        if not isinstance(categories, list):
            categories = [categories]
        if not categories:
            return
        category = self.binder_for(
            'prestashop.product.category').to_odoo(
                categories[0]['id'], unwrap=True)
        return {'categ_id': category.id}

    @mapping
    def categ_ids(self, record):
        categories = record['associations'].get('categories', {}).get(
            self.backend_record.get_version_ps_key('category'), [])
        if not isinstance(categories, list):
            categories = [categories]
        product_categories = []
        for category in categories:
            category_id = self.binder_for(
                'prestashop.product.category').to_odoo(
                    category['id'], unwrap=True).id
            product_categories.append(category_id)

        return {'categ_ids': [(6, 0, product_categories)]}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def ean13(self, record):
        if self.has_combinations(record):
            return {}
        if record['ean13'] in ['', '0']:
            return {}
        if check_ean(record['ean13']):
            return {'ean13': record['ean13']}
        return {}

    def _get_tax_ids(self, record):
        # if record['id_tax_rules_group'] == '0':
        #     return {}
        tax_group = self.binder_for('prestashop.account.tax.group').to_odoo(
            record['id_tax_rules_group'], unwrap=True)
        return tax_group.tax_ids

    @mapping
    def taxes_id(self, record):
        taxes = self._get_tax_ids(record)
        return {'taxes_id': [(6, 0, taxes.ids)]}

    @mapping
    def type(self, record):
        # If the product has combinations, this main product is not a real
        # product. So it is set to a 'service' kind of product. Should better
        # be a 'virtual' product... but it does not exist...
        # The same if the product is a virtual one in prestashop.
        if record['type']['value'] and record['type']['value'] == 'virtual':
            return {"type": 'service'}
        return {"type": 'product'}

    @mapping
    def procure_method(self, record):
        if record['type'] == 'pack':
            return {
                'procure_method': 'make_to_order',
                'supply_method': 'produce',
            }
        return {}

    @mapping
    def extras_manufacturer(self, record):
        mapper = self.unit_for(ManufacturerProductImportMapper)
        return mapper.map_record(record).values(**self.options)

    @mapping
    def tags_to_text(self, record):
        associations = record.get('associations', {})
        tags = associations.get('tags', {}).get(
            self.backend_record.get_version_ps_key('tag'), [])
        tag_adapter = self.unit_for(GenericAdapter, '_prestashop_product_tag')
        if not isinstance(tags, list):
            tags = [tags]
        if tags:
            ps_tags = tag_adapter.search(filters={
                'filter[id]': '[%s]' % '|'.join(x['id'] for x in tags),
                'display': '[name]'
            })
            if ps_tags:
                return {'tags': ','.join(x['name'] for x in ps_tags)}


@prestashop
class ManufacturerProductImportMapper(ImportMapper):
    # For extend in connector_prestashop_manufacturer module, by this way we
    # avoid have dependencies of other modules as procut_manufacturer
    _model_name = 'prestashop.product.template'

    @mapping
    def extras(self, record):
        return {}


class ImportInventory(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = '_import_stock_available'


@prestashop
class ProductInventoryBatchImport(DelayedBatchImporter):
    _model_name = ['_import_stock_available']

    def run(self, filters=None, **kwargs):
        if filters is None:
            filters = {}
        filters['display'] = '[id_product,id_product_attribute]'
        return super(ProductInventoryBatchImport, self).run(filters, **kwargs)

    def _run_page(self, filters, **kwargs):
        records = self.backend_adapter.get(filters)
        for record in records['stock_availables']['stock_available']:
            self._import_record(record, **kwargs)
        return records['stock_availables']['stock_available']

    def _import_record(self, record, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(
            self.session,
            '_import_stock_available',
            self.backend_record.id,
            record,
            **kwargs
        )


@prestashop
class ProductInventoryImport(PrestashopImporter):
    _model_name = ['_import_stock_available']

    def _get_quantity(self, record):
        filters = {
            'filter[id_product]': record['id_product'],
            'filter[id_product_attribute]': record['id_product_attribute'],
            'display': '[quantity]',
        }
        quantities = self.backend_adapter.get(filters)
        all_qty = 0
        quantities = quantities['stock_availables']['stock_available']
        if isinstance(quantities, dict):
            quantities = [quantities]
        for quantity in quantities:
            all_qty += int(quantity['quantity'])
        return all_qty

    def _get_template(self, record):
        if record['id_product_attribute'] == '0':
            binder = self.binder_for('prestashop.product.template')
            return binder.to_odoo(record['id_product'], unwrap=True)
        binder = self.binder_for('prestashop.product.combination')
        return binder.to_odoo(record['id_product_attribute'], unwrap=True)

    def run(self, record):
        self._import_dependency(
            record['id_product'], 'prestashop.product.template')
        if record['id_product_attribute'] != '0':
            self._import_dependency(
                record['id_product_attribute'],
                'prestashop.product.combination')

        qty = self._get_quantity(record)
        if qty < 0:
            qty = 0
        template = self._get_template(record)

        vals = {
            'location_id': self.backend_record.warehouse_id.lot_stock_id.id,
            'product_id': template.id,
            'new_quantity': qty,
        }
        template_qty_id = self.session.env['stock.change.product.qty'].create(
            vals)
        template_qty_id.with_context(
            active_id=template.id).change_product_qty()


@prestashop
class TemplateRecordImport(TranslatableRecordImporter):
    """ Import one translatable record """
    _model_name = [
        'prestashop.product.template',
    ]

    _translatable_fields = {
        'prestashop.product.template': [
            'name',
            'description',
            'link_rewrite',
            'description_short',
            'meta_title',
            'meta_description',
            'meta_keywords',
        ],
    }

    def _after_import(self, erp_id):
        self.import_images(erp_id)
        self.import_combinations()
        self.attribute_line(erp_id)
        self.deactivate_default_product(erp_id)

    def deactivate_default_product(self, erp_id):
        template = erp_id
        if template.product_variant_count != 1:
            for product in template.product_variant_ids:
                if not product.attribute_value_ids:
                    self.env['product.product'].browse(product.id).write(
                        {'active': False})

    def attribute_line(self, erp_id):
        template = erp_id
        attr_line_value_ids = []
        for attr_line in template.attribute_line_ids:
            attr_line_value_ids.extend(attr_line.value_ids.ids)
        template_id = template.odoo_id.id
        products = self.env['product.product'].search([
            ('product_tmpl_id', '=', template_id)]
        )
        if products:
            attribute_ids = []
            for product in products:
                for attribute_value in product.attribute_value_ids:
                    attribute_ids.append(attribute_value.attribute_id.id)
                    # filter unique id for create relation
            for attribute_id in set(attribute_ids):
                values = products.mapped('attribute_value_ids').filtered(
                    lambda x: (x.attribute_id.id == attribute_id and
                               x.id not in attr_line_value_ids))
                if values:
                    self.env['product.attribute.line'].create({
                        'attribute_id': attribute_id,
                        'product_tmpl_id': template_id,
                        'value_ids': [(6, 0, values.ids)],
                    })

    def import_combinations(self):
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get('associations', {})

        ps_key = self.backend_record.get_version_ps_key('combinations')
        combinations = associations.get('combinations', {}).get(ps_key, [])

        if not isinstance(combinations, list):
            combinations = [combinations]
        if combinations:
            first_exec = combinations.pop(
                combinations.index({
                    'id': prestashop_record[
                        'id_default_combination']['value']}))
            if first_exec:
                import_record(
                    self.session, 'prestashop.product.combination',
                    self.backend_record.id, first_exec['id'])

            for combination in combinations:
                import_record(
                    self.session, 'prestashop.product.combination',
                    self.backend_record.id, combination['id'])
            if combinations and associations['images'].get('image', False):
                set_product_image_variant.delay(
                    self.session,
                    'prestashop.product.combination',
                    self.backend_record.id,
                    combinations,
                    priority=15,
                )

    def import_images(self, erp_id):
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get('associations', {})
        images = associations.get('images', {}).get(
            self.backend_record.get_version_ps_key('image'), {})
        if not isinstance(images, list):
            images = [images]
        for image in images:
            if image.get('id'):
                import_product_image.delay(
                    self.session,
                    'prestashop.product.image',
                    self.backend_record.id,
                    prestashop_record['id'],
                    image['id'],
                    priority=10,
                )

    def import_supplierinfo(self, erp_id):
        ps_id = self._get_prestashop_data()['id']
        filters = {
            'filter[id_product]': ps_id,
            'filter[id_product_attribute]': 0
        }
        import_batch(
            self.session,
            'prestashop.product.supplierinfo',
            self.backend_record.id,
            filters=filters
        )
        ps_product_template = erp_id
        ps_supplierinfos = self.env['prestashop.product.supplierinfo'].\
            search([('product_tmpl_id', '=', ps_product_template.id)])
        for ps_supplierinfo in ps_supplierinfos:
            try:
                ps_supplierinfo.resync()
            except PrestaShopWebServiceError:
                ps_supplierinfo.odoo_id.unlink()

    def _import_dependencies(self):
        self._import_default_category()
        self._import_categories()

    def get_template_model_id(self):
        ir_model = self.env['ir.model'].search([
            ('model', '=', 'product.template')], limit=1)
        assert len(ir_model) == 1
        return ir_model.id

    def _import_default_category(self):
        record = self.prestashop_record
        if int(record['id_category_default']):
            try:
                self._import_dependency(record['id_category_default'],
                                        'prestashop.product.category')
            except PrestaShopWebServiceError:
                pass

    def _import_categories(self):
        record = self.prestashop_record
        associations = record.get('associations', {})
        categories = associations.get('categories', {}).get(
            self.backend_record.get_version_ps_key('category'), [])
        if not isinstance(categories, list):
            categories = [categories]
        for category in categories:
            self._import_dependency(
                category['id'], 'prestashop.product.category')


@prestashop
class ProductTemplateBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.product.template'


@job(default_channel='root.prestashop')
def import_inventory(session, backend_id):
    env = get_environment(session, '_import_stock_available', backend_id)
    inventory_importer = env.get_connector_unit(ProductInventoryBatchImport)
    return inventory_importer.run()


@job(default_channel='root.prestashop')
def import_products(session, backend_id, since_date):
    filters = None
    if since_date:
        filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    import_batch(
        session,
        'prestashop.product.category',
        backend_id,
        filters,
        priority=15
    )
    import_batch(
        session,
        'prestashop.product.template',
        backend_id,
        filters,
        priority=15
    )
    session.env['prestashop.backend'].browse(backend_id).write({
        'import_products_since': now_fmt
    })
