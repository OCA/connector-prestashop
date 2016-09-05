# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# A product combination is a product with different attributes in prestashop.
# In prestashop, we can sell a product or a combination of a product with some
# attributes.

# For example, for the iPod product we can found in demo data, it has some
# combinations with different colors and different storage size.

# We map that in OpenERP to a product.product with an attribute.set defined for
# the main product.

from .backend import prestashop
from .unit.backend_adapter import (GenericAdapter)
from .unit.import_synchronizer import PrestashopImportSynchronizer
from .unit.import_synchronizer import TranslatableRecordImport
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper)
from .unit.import_synchronizer import (
    import_batch
)
from openerp.osv.orm import browse_record_list

from openerp.addons.product.product import check_ean
from .unit.backend_adapter import PrestaShopCRUDAdapter

from .product import ProductInventoryExporter

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    PrestaShopWebServiceError = False


@prestashop
class ProductCombinationAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination'
    _prestashop_model = 'combinations'
    _export_node_name = 'combination'


@prestashop
class ProductCombinationRecordImport(PrestashopImportSynchronizer):
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
            self._check_dependency(
                option_value['id_attribute_group'],
                'prestashop.product.combination.option',
            )
            self._check_dependency(
                option_value['id'],
                'prestashop.product.combination.option.value'
            )

    def _after_import(self, erp_id):
        self.import_supplierinfo(erp_id)

    def set_variant_images(self, combinations):
        backend_adapter = self.unit_for(
            PrestaShopCRUDAdapter, 'prestashop.product.combination')
        for combination in combinations:
            try:
                record = backend_adapter.read(combination['id'])
                associations = record.get('associations', {})
                images = associations.get('images', {}).get(
                    self.backend_record.get_version_ps_key('image'), {})
                binder = self.binder_for('prestashop.product.image')
                if not isinstance(images, list):
                    images = [images]
                if 'id' in images[0]:
                    img_ids = [
                        binder.to_odoo(x.get('id'), unwrap=True) for x in
                        images]
                else:
                    img_ids = []
                if img_ids:
                    product_binder = self.binder_for(
                        'prestashop.product.combination')
                    product_product = product_binder.to_odoo(
                        combination['id'], unwrap=True, browse=True)
                    product_product.with_context(
                        connector_no_export=True).write(
                        {'image_ids': [(6, 0, img_ids)]})
            except PrestaShopWebServiceError:
                pass

    def import_supplierinfo(self, erp_id):
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
        ps_product_template = erp_id
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
        template = self.main_template(record)
        return {'product_tmpl_id': template.odoo_id.id}

    @mapping
    def from_main_template(self, record):
        main_template = self.main_template(record)
        result = {}
        for attribute in self.from_main:
            if attribute not in main_template:
                continue
            if hasattr(main_template[attribute], 'id'):
                result[attribute] = main_template[attribute].id
            elif type(main_template[attribute]) is browse_record_list:
                ids = []
                for element in main_template[attribute]:
                    ids.append(element.id)
                result[attribute] = [(6, 0, ids)]
            else:
                result[attribute] = main_template[attribute]
        return result

    def main_template(self, record):
        if hasattr(self, '_main_template'):
            return self._main_template
        template_id = self.get_main_template_id(record)
        self._main_template = self.env['prestashop.product.template'].browse(
            template_id)
        return self._main_template

    def get_main_template_id(self, record):
        template_binder = self.binder_for(
            'prestashop.product.template')
        return template_binder.to_odoo(record['id_product'])

    def _get_option_value(self, record):
        option_values = record['associations']['product_option_values'][
            self.backend_record.get_version_ps_key('product_option_value')]
        if type(option_values) is dict:
            option_values = [option_values]

        for option_value in option_values:
            option_value_binder = self.binder_for(
                'prestashop.product.combination.option.value')
            option_value_odoo_id = option_value_binder.to_odoo(
                option_value['id'])

            option_value_object = self.env[
                'prestashop.product.combination.option.value'].browse(
                option_value_odoo_id
            )
            yield option_value_object

    @mapping
    def name(self, record):
        template = self.main_template(record)
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
            results.append(option_value_object.odoo_id.id)
        return {'attribute_value_ids': [(6, 0, results)]}

    @mapping
    def main_template_id(self, record):
        return {'main_template_id': self.get_main_template_id(record)}

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
        if record['ean13'] in ['', '0']:
            backend_adapter = self.unit_for(
                GenericAdapter, 'prestashop.product.template')
            template = backend_adapter.read(record['id_product'])
            ean13 = template.get('ean13', {})
            if ean13 == '0':
                return {}
            return template['ean13'] and {'ean13': template['ean13']} or {}
        if check_ean(record['ean13']):
            return {'ean13': record['ean13']}
        return {}

    def _get_tax_ids(self, record):
        product_tmpl_binder = self.unit_for(
            GenericAdapter, 'prestashop.product.template')
        tax_group = product_tmpl_binder.read(record['id_product'])
        tax_group = self.binder_for('prestashop.account.tax.group').to_odoo(
            tax_group['id_tax_rules_group'], unwrap=True, browse=True)
        return tax_group.tax_ids

    @mapping
    def specific_price(self, record):
        product = self.binder_for(
            'prestashop.product.combination').to_odoo(
            record['id'], unwrap=True, browse=True)
        product_template = self.binder_for(
            'prestashop.product.template').to_odoo(
                record['id_product'], unwrap=True, browse=True)
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
class ProductCombinationOptionAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination.option'
    _prestashop_model = 'product_options'
    _export_node_name = 'product_options'


@prestashop
class ProductCombinationOptionRecordImport(PrestashopImportSynchronizer):
    _model_name = 'prestashop.product.combination.option'

    def _import_values(self):
        record = self.prestashop_record
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(
            self.backend_record.get_version_ps_key('product_option_value'), [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        for option_value in option_values:
            self._check_dependency(
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
            super(ProductCombinationOptionRecordImport, self).run(ext_id)
        else:
            # else, we create only a prestashop.product.combination.option
            data = {
                'odoo_id': attribute_ids.id,
                'backend_id': self.backend_record.id,
            }
            erp_id = self.model.create(data)
            self.binder.bind(self.prestashop_id, erp_id.id)
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
                    lang['attrs']['id'], browse=True)
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
class ProductCombinationOptionValueRecordImport(TranslatableRecordImport):
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
        attribute_id = binder.to_odoo(
            record['id_attribute_group'], unwrap=True)
        return {'attribute_id': attribute_id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class CombinationInventoryExport(ProductInventoryExporter):
    _model_name = ['prestashop.product.combination']

    def get_filter(self, template):
        return {
            'filter[id_product]': template.main_template_id.prestashop_id,
            'filter[id_product_attribute]': template.prestashop_id,
        }
