# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import models

from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from openerp.addons.connector.unit.mapper import mapping, ImportMapper
from ...unit.importer import (
    PrestashopImporter,
    import_batch,
    TranslatableRecordImporter,
    DelayedBatchImporter,
)
from ...unit.backend_adapter import GenericAdapter, PrestaShopCRUDAdapter
from ...backend import prestashop

import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


@prestashop
class ProductCombinationImporter(PrestashopImporter):
    _model_name = 'prestashop.product.combination'

    def _import_dependencies(self):
        record = self.prestashop_record
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(
            self.backend_record.get_version_ps_key('product_option_value'), [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        backend_adapter = self.unit_for(
            BackendAdapter, 'prestashop.product.combination.option.value')
        for option_value in option_values:
            option_value = backend_adapter.read(option_value['id'])
            self._import_dependency(
                option_value['id_attribute_group'],
                'prestashop.product.combination.option',
            )
            self._import_dependency(
                option_value['id'],
                'prestashop.product.combination.option.value'
            )

    def _after_import(self, binding):
        super(ProductCombinationImporter, self)._after_import(binding)
        self.import_supplierinfo(binding)

    def set_variant_images(self, combinations):
        backend_adapter = self.unit_for(
            PrestaShopCRUDAdapter, 'prestashop.product.combination')
        for combination in combinations:
            try:
                record = backend_adapter.read(combination['id'])
                associations = record.get('associations', {})
                ps_images = associations.get('images', {}).get(
                    self.backend_record.get_version_ps_key('image'), {})
                binder = self.binder_for('prestashop.product.image')
                if not isinstance(ps_images, list):
                    ps_images = [ps_images]
                if 'id' in ps_images[0]:
                    images = [
                        binder.to_odoo(x.get('id'), unwrap=True)
                        for x in ps_images
                    ]
                else:
                    images = []
                if images:
                    product_binder = self.binder_for(
                        'prestashop.product.combination')
                    product_product = product_binder.to_odoo(
                        combination['id'], unwrap=True)
                    product_product.with_context(
                        connector_no_export=True).write(
                        {'image_ids': [(6, 0, images.ids)]})
            except PrestaShopWebServiceError:
                # TODO: why is it silented?
                pass

    def import_supplierinfo(self, binding):
        ps_id = self._get_prestashop_data()['id']
        filters = {
            # 'filter[id_product]': ps_id,
            'filter[id_product_attribute]': ps_id
        }
        import_batch(
            self.session,
            'prestashop.product.supplierinfo',
            self.backend_record.id,
            filters=filters
        )
        ps_product_template = binding
        ps_supplierinfos = self.env['prestashop.product.supplierinfo']. \
            search([('product_tmpl_id', '=', ps_product_template.id)])
        for ps_supplierinfo in ps_supplierinfos:
            try:
                ps_supplierinfo.resync()
            except PrestaShopWebServiceError:
                ps_supplierinfo.odoo_id.unlink()


@prestashop
class ProductCombinationMapper(ImportMapper):
    _model_name = 'prestashop.product.combination'

    direct = [
    ]

    from_main = []

    @mapping
    def combination_default(self, record):
        return {'default_on': bool(int(record['default_on'] or 0))}

    @mapping
    def product_tmpl_id(self, record):
        template = self.get_main_template_binding(record)
        return {'product_tmpl_id': template.odoo_id.id}

    @mapping
    def from_main_template(self, record):
        main_template = self.get_main_template_binding(record)
        result = {}
        for attribute in self.from_main:
            if attribute not in main_template:
                continue
            if hasattr(main_template[attribute], 'id'):
                result[attribute] = main_template[attribute].id
            elif type(main_template[attribute]) is models.BaseModel:
                ids = []
                for element in main_template[attribute]:
                    ids.append(element.id)
                result[attribute] = [(6, 0, ids)]
            else:
                result[attribute] = main_template[attribute]
        return result

    def get_main_template_binding(self, record):
        template_binder = self.binder_for('prestashop.product.template')
        return template_binder.to_odoo(record['id_product'])

    def _get_option_value(self, record):
        option_values = record['associations']['product_option_values'][
            self.backend_record.get_version_ps_key('product_option_value')]
        if type(option_values) is dict:
            option_values = [option_values]

        for option_value in option_values:
            option_value_binder = self.binder_for(
                'prestashop.product.combination.option.value')
            option_value_binding = option_value_binder.to_odoo(
                option_value['id']
            )
            yield option_value_binding.odoo_id

    @mapping
    def name(self, record):
        template = self.get_main_template_binding(record)
        options = []
        for option_value_object in self._get_option_value(record):
            key = option_value_object.attribute_id.name
            value = option_value_object.name
            options.append('%s:%s' % (key, value))
        return {'name_template': template.name}

    @mapping
    def attribute_value_ids(self, record):
        results = []
        for option_value_object in self._get_option_value(record):
            results.append(option_value_object.id)
        return {'attribute_value_ids': [(6, 0, results)]}

    @mapping
    def main_template_id(self, record):
        template_binding = self.get_main_template_binding(record)
        return {'main_template_id': template_binding.id}

    def _template_code_exists(self, code):
        model = self.session.env['product.product']
        combination_binder = self.binder_for('prestashop.product.combination')
        template_ids = model.search([
            ('default_code', '=', code),
            ('company_id', '=', self.backend_record.company_id.id),
        ], limit=1)
        return template_ids and not combination_binder.to_backend(
            template_ids, wrap=True)

    @mapping
    def default_code(self, record):
        code = record.get('reference')
        if not code:
            code = "%s_%s" % (record['id_product'], record['id'])
        if not self._template_code_exists(code):
            return {'default_code': code}
        i = 1
        current_code = '%s_%s' % (code, i)
        while self._template_code_exists(current_code):
            i += 1
            current_code = '%s_%s' % (code, i)
        return {'default_code': current_code}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def ean13(self, record):
        barcode = None
        check_ean = self.env['barcode.nomenclature'].check_ean
        if record['ean13'] in ['', '0']:
            backend_adapter = self.unit_for(
                GenericAdapter, 'prestashop.product.template')
            template = backend_adapter.read(record['id_product'])
            ean13 = template.get('ean13')
            if ean13 and ean13 != '0' and check_ean(template['ean13']):
                barcode = ean13
        elif self.env['barcode.nomenclature'].check_ean(record['ean13']):
            barcode = record['ean13']
        if barcode:
            return {'barcode': ean13}
        return {}

    def _get_tax_ids(self, record):
        product_tmpl_adapter = self.unit_for(
            GenericAdapter, 'prestashop.product.template')
        tax_group = product_tmpl_adapter.read(record['id_product'])
        tax_group = self.binder_for('prestashop.account.tax.group').to_odoo(
            tax_group['id_tax_rules_group'], unwrap=True)
        return tax_group.tax_ids

    @mapping
    def specific_price(self, record):
        product = self.binder_for(
            'prestashop.product.combination').to_odoo(
            record['id'], unwrap=True
        )
        product_template = self.binder_for(
            'prestashop.product.template').to_odoo(
                record['id_product'], unwrap=True
        )
        tax = product.product_tmpl_id.taxes_id[:1] or self._get_tax_ids(record)
        factor_tax = tax.price_include and (1 + tax.amount) or 1.0
        impact = float(record['price']) * factor_tax
        cost_price = float(record['wholesale_price'])
        return {
            'list_price': product_template.list_price,
            'standard_price': cost_price or product_template.standard_price,
            'impact_price': impact
        }


@prestashop
class ProductCombinationOptionImporter(PrestashopImporter):
    _model_name = 'prestashop.product.combination.option'

    def _import_values(self):
        record = self.prestashop_record
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(
            self.backend_record.get_version_ps_key('product_option_value'), [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        for option_value in option_values:
            self._import_dependency(
                option_value['id'],
                'prestashop.product.combination.option.value'
            )

    def run(self, ext_id):
        # looking for an product.attribute with the same name
        self.prestashop_id = ext_id
        self.prestashop_record = self._get_prestashop_data()
        name = self.mapper.name(self.prestashop_record)['name']
        attribute_ids = self.env['product.attribute'].search([
            ('name', '=', name),
        ])
        if len(attribute_ids) == 0:
            # if we don't find it, we create a prestashop_product_combination
            super(ProductCombinationOptionImporter, self).run(ext_id)
        else:
            # else, we create only a prestashop.product.combination.option
            data = {
                'odoo_id': attribute_ids.id,
                'backend_id': self.backend_record.id,
            }
            erp_id = self.model.create(data)
            self.binder.bind(self.prestashop_id, erp_id)
        self._import_values()


@prestashop
class ProductCombinationOptionMapper(ImportMapper):
    _model_name = 'prestashop.product.combination.option'

    direct = []

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def name(self, record):
        name = None
        if 'language' in record['name']:
            language_binder = self.binder_for('prestashop.res.lang')
            languages = record['name']['language']
            if not isinstance(languages, list):
                languages = [languages]
            for lang in languages:
                erp_language = language_binder.to_odoo(
                    lang['attrs']['id'])
                if not erp_language:
                    continue
                if erp_language.code == 'en_US':
                    name = lang['value']
                    break
            if name is None:
                name = languages[0]['value']
        else:
            name = record['name']
        return {'name': name}


@prestashop
class ProductCombinationOptionValueAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination.option.value'
    _prestashop_model = 'product_option_values'
    _export_node_name = 'product_option_value'


@prestashop
class ProductCombinationOptionValueImporter(TranslatableRecordImporter):
    _model_name = 'prestashop.product.combination.option.value'

    _translatable_fields = {
        'prestashop.product.combination.option.value': ['name'],
    }


@prestashop
class ProductCombinationOptionValueMapper(ImportMapper):
    _model_name = 'prestashop.product.combination.option.value'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def attribute_id(self, record):
        binder = self.binder_for('prestashop.product.combination.option')
        attribute = binder.to_odoo(record['id_attribute_group'], unwrap=True)
        return {'attribute_id': attribute.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class ProductProductBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.product.product'
