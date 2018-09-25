# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, models, api
from odoo.addons.queue_job.job import job
# from odoo.addons.connector.components.mapper import (
#     mapping,
#     only_create,
# )
# from ...components.importer import (
#     import_record,
#     import_batch,
# )
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping, external_to_m2o, only_create)
from odoo.exceptions import ValidationError


import datetime
import logging
_logger = logging.getLogger(__name__)

try:
    import html2text
except ImportError:
    _logger.debug('Cannot import `html2text`')

try:
    from bs4 import BeautifulSoup
except ImportError:
    _logger.debug('Cannot import `bs4`')

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug('Cannot import from `prestapyt`')


class TemplateMapper(Component):
    _name = 'prestashop.product.template.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.template'

    direct = [
        ('weight', 'weight'),
        ('wholesale_price', 'wholesale_price'),
        ('wholesale_price', 'standard_price'),
        (external_to_m2o('id_shop_default'), 'default_shop_id'),
        ('link_rewrite', 'link_rewrite'),
        ('reference', 'reference'),
        ('available_for_order', 'available_for_order'),
        ('on_sale', 'on_sale'),
    ]

    def _apply_taxes(self, tax, price):
        if self.backend_record.taxes_included == tax.price_include:
            return price
        factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
        if self.backend_record.taxes_included:
            if not tax.price_include:
                return price / factor_tax
        else:
            if tax.price_include:
                return price * factor_tax

    @mapping
    def list_price(self, record):
        price = 0.0
        tax = self._get_tax_ids(record)
        if record['price'] != '':
            price = float(record['price'])
        price = self._apply_taxes(tax, price)
        return {'list_price': price}

    @mapping
    def tags_to_text(self, record):
        associations = record.get('associations', {})
        tags = associations.get('tags', {}).get(
            self.backend_record.get_version_ps_key('tag'), [])
        tag_adapter = self.component(
            usage='backend.adapter', model_name='_prestashop_product_tag'
        )
        if not isinstance(tags, list):
            tags = [tags]
        if tags:
            ps_tags = tag_adapter.search(filters={
                'filter[id]': '[%s]' % '|'.join(x['id'] for x in tags),
                'display': '[name]'
            })
            if ps_tags:
                return {'tags': ','.join(x['name'] for x in ps_tags)}

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']}
        return {'name': 'noname'}

    @mapping
    def date_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date_add': datetime.datetime.now()}
        return {'date_add': record['date_add']}

    @mapping
    def date_upd(self, record):
        if record['date_upd'] == '0000-00-00 00:00:00':
            return {'date_upd': datetime.datetime.now()}
        return {'date_upd': record['date_upd']}

    def has_combinations(self, record):
        associations = record.get('associations', {})
        combinations = associations.get('combinations', {}).get(
            self.backend_record.get_version_ps_key('combinations'))
        return len(combinations or '') != 0

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the product to an existing one with the same code """
#         product = self.env['product.template'].search(
#             [('default_code', '=', record['reference'])], limit=1)
#         if product:
#             return {'odoo_id': product.id}
        if self.backend_record.matching_product_template:
            if self.has_combinations(record):
                # Browse combinations for matching products and find if there
                # is a potential template to be matched
                template = self.env['product.template']
                associations = record.get('associations', {})
                combinations = associations.get('combinations', {}).get(
                    self.backend_record.get_version_ps_key('combinations'))
                if len(combinations) == 1:
                    # Defensive mode when product have no combinations, force
                    # the list mode
                    combinations = [combinations]
                for prod in combinations:
                    backend_adapter = self.component(
                        usage='backend.adapter',
                        model_name='prestashop.product.combination')
                    variant = backend_adapter.read(int(prod['id']))
                    code = variant.get(self.backend_record.matching_product_ch)
                    if self.backend_record.matching_product_ch == 'reference':
                        product = self.env['product.product'].search(
                            [('default_code', '=', code)])
                        if len(product) > 1:
                            raise ValidationError(_(
                                'Error! Multiple products found with '
                                'combinations reference %s. Maybe consider to '
                                'update you datas') % code)
                        template |= product.product_tmpl_id
                    if self.backend_record.matching_product_ch == 'barcode':
                        product = self.env['product.product'].search(
                            [('barcode', '=', code)])
                        if len(product) > 1:
                            raise ValidationError(_(
                                'Error! Multiple products found with '
                                'combinations reference %s. Maybe consider to '
                                'update you datas') % code)
                        template |= product.product_tmpl_id
                _logger.debug('template %s' % template)
                if len(template) == 1:
                    return {'odoo_id': template.id}
                if len(template) > 1:
                    raise ValidationError(_(
                        'Error! Multiple templates are found with '
                        'combinations reference. Maybe consider to change '
                        'matching option'))
            else:
                code = record.get(self.backend_record.matching_product_ch)
                if self.backend_record.matching_product_ch == 'reference':
                    if code:
                        if self._template_code_exists(code):
                            product = self.env['product.template'].search(
                                [('default_code', '=', code)], limit=1)
                            if product:
                                return {'odoo_id': product.id}

                if self.backend_record.matching_product_ch == 'barcode':
                    if code:
                        product = self.env['product.template'].search(
                            [('barcode', '=', code)], limit=1)
                        if product:
                            return {'odoo_id': product.id}
        return {}

    def _template_code_exists(self, code):
        model = self.env['product.template']
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

    @staticmethod
    def sanitize_html(content):
        content = BeautifulSoup(content, 'html.parser')
        # Prestashop adds both 'lang="fr-ch"' and 'xml:lang="fr-ch"'
        # but Odoo tries to parse the xml for the translation and fails
        # due to the unknow namespace
        for child in content.find_all(lambda tag: tag.has_attr('xml:lang')):
            del child['xml:lang']
        return content.prettify()

    @mapping
    def descriptions(self, record):
        return {
            'description': self.clear_html_field(
                record.get('description_short', '')),
            'description_html': self.sanitize_html(
                record.get('description', '')),
            'description_short_html': self.sanitize_html(
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
    def categ_ids(self, record):
        categories = record['associations'].get('categories', {}).get(
            self.backend_record.get_version_ps_key('category'), [])
        if not isinstance(categories, list):
            categories = [categories]
        product_categories = self.env['product.category'].browse()
        binder = self.binder_for('prestashop.product.category')
        for ps_category in categories:
            product_categories |= binder.to_internal(
                ps_category['id'],
                unwrap=True,
            )
        return {'categ_ids': [(6, 0, product_categories.ids)]}

    @mapping
    def default_category_id(self, record):
        if not int(record['id_category_default']):
            return
        binder = self.binder_for('prestashop.product.category')
        category = binder.to_internal(
            record['id_category_default'],
            unwrap=True,
        )
        if category:
            return {'prestashop_default_category_id': category.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def barcode(self, record):
        if self.has_combinations(record):
            return {}
        barcode = record.get('barcode') or record.get('ean13')
        if barcode in ['', '0']:
            return {}
        if self.env['barcode.nomenclature'].check_ean(barcode):
            return {'barcode': barcode}
        return {}

    def _get_tax_ids(self, record):
        # if record['id_tax_rules_group'] == '0':
        #     return {}
        binder = self.binder_for('prestashop.account.tax.group')
        tax_group = binder.to_internal(
            record['id_tax_rules_group'],
            unwrap=True,
        )
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
# TODO FIXME
#    @mapping
#    def extras_features(self, record):
#        mapper = self.component(usage='feature.product.import.mapper')
#        return mapper.map_record(record).values(**self.options)
#
#    @mapping
#    def extras_manufacturer(self, record):
#        mapper = self.component(usage='manufacturer.product.import.mapper')
#        return mapper.map_record(record).values(**self.options)


class FeaturesProductImportMapper(Component):
    # To extend in connector_prestashop_feature module. In this way we
    # dependencies on other modules like product_custom_info
    _name = 'prestashop.feature.product.template.mapper'
    _inherit = 'prestashop.product.template.mapper'
    _apply_on = 'prestashop.product.template'
    _usage = 'feature.product.import.mapper'

    @mapping
    def extras_features(self, record):
        return {}


class ManufacturerProductImportMapper(Component):
    # To extend in connector_prestashop_manufacturer module. In this way we
    # dependencies on other modules like product_manufacturer
    _name = 'prestashop.manufacturer.product.template.mapper'
    _inherit = 'prestashop.product.template.mapper'
    _apply_on = 'prestashop.product.template'
    _usage = 'manufacturer.product.import.mapper'

    @mapping
    def extras_manufacturer(self, record):
        return {}


class ImportInventory(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = '_import_stock_available'

    @job(default_channel='root.prestashop')
    @api.model
    def import_record(self, backend, prestashop_id, record=None, **kwargs):
        """ Import a record from PrestaShop """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(prestashop_id, record=record, **kwargs)


class ProductInventoryBatchImporter(Component):
    _name = 'prestashop._import_stock_available.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = '_import_stock_available'

    def run(self, filters=None, **kwargs):
        if filters is None:
            filters = {}
        filters['display'] = '[id,id_product,id_product_attribute]'
        _super = super(ProductInventoryBatchImporter, self)
        return _super.run(filters, **kwargs)

    def _run_page(self, filters, **kwargs):
        records = self.backend_adapter.get(filters)
        for record in records['stock_availables']['stock_available']:
            # if product has combinations then do not import product stock
            # since combination stocks will be imported
            if record['id_product_attribute'] == '0':
                combination_stock_ids = self.backend_adapter.search({
                    'filter[id_product]': record['id_product'],
                    'filter[id_product_attribute]': '>[0]',
                })
                if combination_stock_ids:
                    continue
            self._import_record(record['id'], record=record, **kwargs)
        return records['stock_availables']['stock_available']

    def _import_record(self, record_id, record=None, **kwargs):
        """ Delay the import of the records"""
        assert record
        self.env['_import_stock_available'].with_delay().import_record(
            self.backend_record,
            record_id,
            record=record,
            **kwargs
        )


class ProductInventoryImporter(Component):
    _name = 'prestashop._import_stock_available.importer'
    _inherit = 'prestashop.importer'
    _apply_on = '_import_stock_available'

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

    def _get_binding(self):
        record = self.prestashop_record
        if record['id_product_attribute'] == '0':
            binder = self.binder_for('prestashop.product.template')
            return binder.to_internal(record['id_product'])
        binder = self.binder_for('prestashop.product.combination')
        return binder.to_internal(record['id_product_attribute'])

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.prestashop_record
        self._import_dependency(
            record['id_product'], 'prestashop.product.template'
        )
        if record['id_product_attribute'] != '0':
            self._import_dependency(
                record['id_product_attribute'],
                'prestashop.product.combination'
            )

    def _check_in_new_connector_env(self):
        # not needed in this importer
        return

    def run(self, prestashop_id, record=None, **kwargs):
        assert record
        self.prestashop_record = record
        return super(ProductInventoryImporter, self).run(
            prestashop_id, **kwargs
        )

    def _import(self, binding, **kwargs):
        record = self.prestashop_record
        qty = self._get_quantity(record)
        if qty < 0:
            qty = 0
        if binding._name == 'prestashop.product.template':
            products = binding.odoo_id.product_variant_ids
        else:
            products = binding.odoo_id

        location = (self.backend_record.stock_location_id or
                    self.backend_record.warehouse_id.lot_stock_id)
        for product in products:
            vals = {
                'location_id': location.id,
                'product_id': product.id,
                'new_quantity': qty,
            }
            template_qty = self.env['stock.change.product.qty'].create(vals)
            template_qty.with_context(
                active_id=product.id,
                connector_no_export=True,
            ).change_product_qty()


class ProductTemplateImporter(Component):
    """ Import one translatable record """
    _name = 'prestashop.product.template.importer'
    _inherit = 'prestashop.translatable.record.importer'
    _apply_on = 'prestashop.product.template'

    _base_mapper = TemplateMapper

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

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(ProductTemplateImporter, self).__init__(environment)
        self.default_category_error = False

    def _after_import(self, binding):
        super(ProductTemplateImporter, self)._after_import(binding)
        self.import_images(binding)
        self.import_combinations()
        self.attribute_line(binding)
        self.deactivate_default_product(binding)
        self.checkpoint_default_category_missing(binding)

    def checkpoint_default_category_missing(self, binding):
        if self.default_category_error:
            msg = _('The default category could not be imported.')
            self.backend_record.add_checkpoint(
                binding,
                message=msg,
            )

    def deactivate_default_product(self, binding):
        if binding.product_variant_count != 1:
            for product in binding.product_variant_ids:
                if not product.attribute_value_ids:
                    self.env['product.product'].browse(product.id).write(
                        {'active': False})

    def attribute_line(self, binding):
        attr_line_value_ids = []
        for attr_line in binding.attribute_line_ids:
            attr_line_value_ids.extend(attr_line.value_ids.ids)
        template_id = binding.odoo_id.id
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

    def _import_combination(self, combination, **kwargs):
        """ Import a combination

        Can be overriden for instance to forward arguments to the importer
        """
        self._import_dependency(combination['id'],
                                'prestashop.product.combination',
                                always=True,
                                **kwargs)

    def _delay_product_image_variant(self, combinations, **kwargs):
        delayable = self.env['prestashop.product.combination'].with_delay(
            priority=15)
        delayable.set_product_image_variant(
            self.backend_record,
            combinations,
            **kwargs)

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
                self._import_combination(first_exec)

            for combination in combinations:
                self._import_combination(combination)

            if combinations and associations['images'].get('image'):
                self._delay_product_image_variant([first_exec] + combinations)

    def import_images(self, binding):
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get('associations', {})
        images = associations.get('images', {}).get(
            self.backend_record.get_version_ps_key('image'), {})
        if not isinstance(images, list):
            images = [images]
        for image in images:
            if image.get('id'):
                delayable = self.env['prestashop.product.image'].with_delay(
                    priority=10)
                delayable.import_product_image(
                    self.backend_record,
                    prestashop_record['id'],
                    image['id'])

    def import_supplierinfo(self, binding):
        ps_id = self._get_prestashop_data()['id']
        filters = {
            'filter[id_product]': ps_id,
            'filter[id_product_attribute]': 0
        }
        self.env['prestashop.product.supplierinfo'].with_delay().import_batch(
            self.backend_record,
            filters=filters
        )
        ps_product_template = binding
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
        self._import_manufacturer()

    def _import_manufacturer(self):
        self.component(
            usage='manufacturer.product.importer').import_manufacturer(
                self.prestashop_record.get('id_manufacturer'))

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
                # a checkpoint will be added in _after_import (because
                # we'll know the binding at this point)
                self.default_category_error = True

    def _import_categories(self):
        record = self.prestashop_record
        associations = record.get('associations', {})
        categories = associations.get('categories', {}).get(
            self.backend_record.get_version_ps_key('category'), [])
        if not isinstance(categories, list):
            categories = [categories]
        for category in categories:
            self._import_dependency(category['id'],
                                    'prestashop.product.category')


class ManufacturerProductDependency(Component):
    # To extend in connector_prestashop_feature module. In this way we
    # dependencies on other modules like product_manufacturer
    _name = 'prestashop.product.template.manufacturer.importer'
    _inherit = 'prestashop.product.template.importer'
    _apply_on = 'prestashop.product.template'
    _usage = 'manufacturer.product.importer'

    def import_manufacturer(self, manufacturer_id):
        return


class ProductTemplateBatchImporter(Component):
    _name = 'prestashop.product.template.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = 'prestashop.product.template'
