from unidecode import unidecode

from openerp.osv import fields, orm
from backend import prestashop
from .unit.backend_adapter import GenericAdapter
from .unit.import_synchronizer import PrestashopImportSynchronizer
from .unit.import_synchronizer import TranslatableRecordImport
from .unit.mapper import PrestashopImportMapper
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from openerp.addons.connector.unit.mapper import mapping


class product_product(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'prestashop_combinations_bind_ids': fields.one2many(
            'prestashop.product.combination',
            'openerp_id',
            string='PrestaShop Bindings (combinations)'
        ),
    }


class prestashop_product_combination(orm.Model):
    _name = 'prestashop.product.combination'
    _inherit = 'prestashop.binding'
    _inherits = {'product.product': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'product.product',
            string='Product',
            required=True,
            ondelete='cascade'
        ),
        'main_product_id': fields.many2one(
            'prestashop.product.product',
            string='Main product',
            required=True,
            ondelete='cascade'
        ),
    }


@prestashop
class ProductCombinationAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination'
    _prestashop_model = 'combinations'


@prestashop
class ProductCombinationRecordImport(PrestashopImportSynchronizer):
    _model_name = 'prestashop.product.combination'

    def _import_dependencies(self):
        record = self.prestashop_record
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get('product_option_value', [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        for option_value in option_values:
            backend_adapter = self.get_connector_unit_for_model(
                BackendAdapter,
                'prestashop.product.combination.option.value'
            )
            option_value = backend_adapter.read(option_value['id'])
            self._check_dependency(
                option_value['id_attribute_group'],
                'prestashop.product.combination.option',
            )

            self.check_location(option_value)

    def check_location(self, option_value):
        option_binder = self.get_binder_for_model(
            'prestashop.product.combination.option')
        attribute_id = option_binder.to_openerp(
            option_value['id_attribute_group'], True)
        product = self.mapper.main_product(self.prestashop_record)
        attribute_group_id = product.attribute_set_id.attribute_group_ids[0].id

        attribute_location_model = self.session.pool.get('attribute.location')
        attribute_location_ids = attribute_location_model.search(
            self.session.cr,
            self.session.uid,
            [
                ('attribute_id', '=', attribute_id),
                ('attribute_group_id', '=', attribute_group_id)
            ]
        )
        if not attribute_location_ids:
            attribute_location_model.create(
                self.session.cr,
                self.session.uid,
                {
                    'attribute_id': attribute_id,
                    'attribute_group_id': attribute_group_id,
                }
            )


@prestashop
class ProductCombinationMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.combination'

    direct = [
        ('weight', 'weight'),
        ('wholesale_price', 'standard_price'),
        ('price', 'lst_price'),
    ]

    from_main = [
        'name',
        'categ_id',
        'categ_ids',
        'taxes_ids',
        'type',
        'company_id',
    ]

    @mapping
    def from_main_product(self, record):
        main_product = self.main_product(record)
        result = {}
        for attribute in self.from_main:
            if attribute not in main_product:
                continue
            if hasattr(main_product[attribute], 'id'):
                result[attribute] = main_product[attribute].id
            elif type(main_product[attribute]) is list:
                ids = []
                for element in main_product[attribute]:
                    ids.append(element.id)
                result[attribute] = [(6, 0, ids)]
            else:
                result[attribute] = main_product[attribute]
        return result

    def main_product(self, record):
        if hasattr(self, '_main_product'):
            return self._main_product
        product_model = self.environment.session.pool.get(
            'prestashop.product.product')
        product_id = self.get_main_product_id(record)
        self._main_product = product_model.browse(
            self.session.cr,
            self.session.uid,
            product_id
        )
        return self._main_product

    def get_main_product_id(self, record):
        product_binder = self.get_binder_for_model(
            'prestashop.product.product')
        return product_binder.to_openerp(record['id_product'])

    @mapping
    def attribute_set_id(self, record):
        product = self.main_product(record)
        if 'attribute_set_id' in product:
            return {'attribute_set_id': product.attribute_set_id.id}
        return {}

    @mapping
    def attributes_values(self, record):
        option_values = record['associations']['product_option_values'][
            'product_option_value']
        if type(option_values) is dict:
            option_values = [option_values]

        results = {}
        for option_value in option_values:

            option_value_binder = self.get_binder_for_model(
                'prestashop.product.combination.option.value')
            option_value_openerp_id = option_value_binder.to_openerp(
                option_value['id'])

            option_value_model = self.environment.session.pool.get(
                'prestashop.product.combination.option.value')
            option_value_object = option_value_model.browse(
                self.session.cr,
                self.session.uid,
                option_value_openerp_id
            )
            field_name = option_value_object.attribute_id.name
            results[field_name] = option_value_object.id
        return results

    @mapping
    def main_product_id(self, record):
        return {'main_product_id': self.get_main_product_id(record)}

    def _product_code_exists(self, code):
        model = self.session.pool.get('product.product')
        product_ids = model.search(self.session.cr, self.session.uid, [
            ('default_code', '=', code)
        ])
        return len(product_ids) > 0

    @mapping
    def default_code(self, record):
        if not record.get('reference'):
            return {}
        code = record.get('reference')
        if not self._product_code_exists(code):
            return {'default_code': code}
        i = 1
        current_code = '%s_%d' % (code, i)
        while self._product_code_exists(current_code):
            i += 1
            current_code = '%s_%d' % (code, i)
        return {'default_code': current_code}

    ##@mapping
    ##def active(self, record):
    ##    return {'always_available': bool(int(record['active']))}

    ##@mapping
    ##def sale_ok(self, record):
    ##    return {'sale_ok': record['available_for_order'] == '1'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def ean13(self, record):
        if record['ean13'] == '0':
            return {}
        return {'ean13': record['ean13']}


class attribute_attribute(orm.Model):
    _inherit = 'attribute.attribute'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.combination.option',
            'openerp_id',
            string='PrestaShop Bindings (combinations)'
        ),
    }


class prestashop_product_combination_option(orm.Model):
    _name = 'prestashop.product.combination.option'
    _inherit = 'prestashop.binding'
    _inherits = {'attribute.attribute': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'attribute.attribute',
            string='Attribute',
            required=True,
            ondelete='cascade'
        ),
    }


@prestashop
class ProductCombinationOptionAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination.option'
    _prestashop_model = 'product_options'


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
        super(ProductCombinationOptionRecordImport, self).run(ext_id)

        self._import_values()


@prestashop
class ProductCombinationOptionMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.combination.option'

    @mapping
    def attribute_type(self, record):
        return {'attribute_type': 'select'}

    @mapping
    def model_id(self, record):
        model = self.environment.session.pool.get('ir.model')
        ids = model.search(
            self.session.cr,
            self.session.uid,
            [('model', '=', 'product.product')]
        )
        assert len(ids) == 1
        return {'model_id': ids[0], 'model': 'product.product'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def name(self, record):
        name = None
        if 'language' in record['name']:
            language_binder = self.get_binder_for_model('prestashop.res.lang')
            model = self.environment.session.pool.get('prestashop.res.lang')
            languages = record['name']['language']
            if type(languages) != list:
                languages = [languages]
            for lang in languages:
                erp_language_id = language_binder.to_openerp(
                    lang['attrs']['id'])
                erp_lang = model.read(
                    self.session.cr,
                    self.session.uid,
                    erp_language_id,
                )
                if erp_lang['code'] == 'en_US':
                    name = lang['value']
                    break
            if name is None:
                name = languages[0]['value']
        else:
            name = record['name']
        field_name = 'x_' + unidecode(name.replace(' ', ''))
        return {'name': field_name, 'field_description': name}


class attribute_option(orm.Model):
    _inherit = 'attribute.option'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.product.combination.option.value',
            'openerp_id',
            string='PrestaShop Bindings'
        ),
    }


class prestashop_product_combination_option_value(orm.Model):
    _name = 'prestashop.product.combination.option.value'
    _inherit = 'prestashop.binding'
    _inherits = {'attribute.option': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'attribute.option',
            string='Attribute',
            required=True,
            ondelete='cascade'
        ),
    }


@prestashop
class ProductCombinationOptionValueAdapter(GenericAdapter):
    _model_name = 'prestashop.product.combination.option.value'
    _prestashop_model = 'product_option_values'


@prestashop
class ProductCombinationOptionValueRecordImport(TranslatableRecordImport):
    _model_name = 'prestashop.product.combination.option.value'

    _translatable_fields = {
        'prestashop.product.combination.option.value': ['name'],
    }


@prestashop
class ProductCombinationOptionValueMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.combination.option.value'

    direct = [
        ('name', 'name'),
        ('position', 'sequence'),
    ]

    @mapping
    def attribute_id(self, record):
        binder = self.get_binder_for_model(
            'prestashop.product.combination.option')
        attribute_id = binder.to_openerp(record['id_attribute_group'], True)
        return {'attribute_id': attribute_id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
