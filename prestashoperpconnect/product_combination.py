'''
A product combination is a product with different attributes in prestashop.
In prestashop, we can sell a product or a combination of a product with some
attributes.

For example, for the iPod product we can found in demo data, it has some
combinations with different colors and different storage size.

We map that in OpenERP to a product.product with an attribute.set defined for
the main product.
'''

from unidecode import unidecode
import json

from openerp import SUPERUSER_ID
from openerp.osv import fields, orm
from backend import prestashop
from .unit.backend_adapter import GenericAdapter
from .unit.import_synchronizer import PrestashopImportSynchronizer
from .unit.import_synchronizer import TranslatableRecordImport
from .unit.import_synchronizer import import_batch
from .unit.mapper import PrestashopImportMapper
from .unit.import_synchronizer import import_record
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from openerp.addons.connector.unit.mapper import mapping
from openerp.osv.orm import browse_record_list

from openerp.addons.product.product import check_ean
from .unit.backend_adapter import PrestaShopCRUDAdapter

from .product import ProductInventoryExport

from prestapyt import PrestaShopWebServiceError

try:
    from xml.etree import cElementTree as ElementTree
except ImportError, e:
    from xml.etree import ElementTree


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
            'product_option_values', {}).get('product_option_value', [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        backend_adapter = self.get_connector_unit_for_model(
            BackendAdapter,
            'prestashop.product.combination.option.value'
        )
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
        record = self.prestashop_record


@prestashop
class ProductCombinationMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.combination'

    direct = [
        ('default_on', 'default_on'),
    ]

    from_main = []

    @mapping
    def image_variant(self, record):
        associations = record.get('associations', {})
        images = associations.get('images', {}).get('image', {})
        if not isinstance(images, list):
            images = [images]
        if images[0].get('id'):
            binder = self.get_binder_for_model('prestashop.product.image')
            image_id = binder.to_openerp(images[0].get('id'))
            variant_image = self.session.browse('prestashop.product.image',
                                                image_id)
            if variant_image:
                if not variant_image.link:
                    return {'image_variant': variant_image.file_db_store}
                else:
                    adapter = self.get_connector_unit_for_model(
                        PrestaShopCRUDAdapter,
                        'prestashop.product.image')
                    try:
                        image = adapter.read(images[0].get('id'),
                                             record['value'])
                        return {'image_variant': image['content']}
                    except PrestaShopWebServiceError:
                        pass
                    except IOError:
                        pass

    @mapping
    def product_tmpl_id(self, record):
        template = self.main_template(record)
        return {'product_tmpl_id': template.openerp_id.id}

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
        self._main_template = self.session.browse(
            'prestashop.product.template',
            template_id)
        return self._main_template

    def get_main_template_id(self, record):
        template_binder = self.get_binder_for_model(
            'prestashop.product.template')
        return template_binder.to_openerp(record['id_product'])

    def _get_option_value(self, record):
        option_values = record['associations']['product_option_values'][
            'product_option_value']
        if type(option_values) is dict:
            option_values = [option_values]

        for option_value in option_values:
            option_value_binder = self.get_binder_for_model(
                'prestashop.product.combination.option.value')
            option_value_openerp_id = option_value_binder.to_openerp(
                option_value['id'])

            option_value_object = self.session.browse(
                'prestashop.product.combination.option.value',
                option_value_openerp_id
            )
            yield option_value_object

    @mapping
    def name(self, record):
        # revisar el estado de las caracteristicas
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
            results.append(option_value_object.openerp_id.id)
        return {'attribute_value_ids': [(6, 0, results)]}

    @mapping
    def main_template_id(self, record):
        return {'main_template_id': self.get_main_template_id(record)}

    def _template_code_exists(self, code):
        model = self.session.pool.get('product.template')
        template_ids = model.search(self.session.cr, SUPERUSER_ID, [
            ('default_code', '=', code),
            ('company_id', '=', self.backend_record.company_id.id),
        ])
        return len(template_ids) > 0

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
            backend_adapter = self.get_connector_unit_for_model(
            GenericAdapter, 'prestashop.product.template')
            template = backend_adapter.read(record['id_product'])
            return template['ean13'] and {'ean13': template['ean13']} or {}
        if check_ean(record['ean13']):
            return {'ean13': record['ean13']}
        return {}


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
            'product_option_values', {}).get('product_option_value', [])
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
        attribute_ids = self.session.search('product.attribute',
                                            [('name', '=', name)])
        if len(attribute_ids) == 0:
            # if we don't find it, we create a prestashop_product_combination
            super(ProductCombinationOptionRecordImport, self).run(ext_id)
        else:
            # else, we create only a prestashop.product.combination.option
            context = self._context()
            data = {
                'openerp_id': attribute_ids[0],
                'backend_id': self.backend_record.id,
            }
            erp_id = self.model.create(self.session.cr, self.session.uid,
                                       data, context)
            self.binder.bind(self.prestashop_id, erp_id)

        self._import_values()


@prestashop
class ProductCombinationOptionMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.combination.option'

    direct = []

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def name(self, record):
        name = None
        if 'language' in record['name']:
            language_binder = self.get_binder_for_model('prestashop.res.lang')
            languages = record['name']['language']
            if not isinstance(languages, list):
                languages = [languages]
            for lang in languages:
                erp_language_id = language_binder.to_openerp(
                    lang['attrs']['id'])
                if not erp_language_id:
                    continue
                erp_lang = self.session.read(
                    'prestashop.res.lang',
                    erp_language_id,
                    []
                )
                if erp_lang['code'] == 'en_US':
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
class ProductCombinationOptionValueMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.combination.option.value'

    direct = []

    @mapping
    def name(self, record):
        name = None
        duplicate_name = self.session.search('product.attribute.value',
                                             [('name', '=', record['name'])])
        if duplicate_name:
            name = "%s-%s" % (record['name'], record['id'])
        else:
            name = record['name']
        return {'name': name}

    @mapping
    def attribute_id(self, record):
        binder = self.get_binder_for_model(
            'prestashop.product.combination.option')
        attribute_id = binder.to_openerp(record['id_attribute_group'],
                                         unwrap=True)
        return {'attribute_id': attribute_id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class CombinationInventoryExport(ProductInventoryExport):
    _model_name = ['prestashop.product.combination']

    def get_filter(self, template):
        return {
            'filter[id_template': template.main_template_id.prestashop_id,
            'filter[id_product_attribute]': template.prestashop_id,
        }
