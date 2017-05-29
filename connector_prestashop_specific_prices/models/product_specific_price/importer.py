# -*- coding: utf-8 -*-
# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import exceptions, _
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.importer import (
    PrestashopImporter, DelayedBatchImporter
)
from openerp.addons.connector.unit.mapper import (
    ImportMapper, mapping
)


@prestashop
class ProductPricelistItemMapper(ImportMapper):
    _model_name = 'prestashop.specific.price'

    @mapping
    def based_on(self, record):
        return {'base': self.env.ref('product.list_price').id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def product_id(self, record):
        vals = {}
        if int(record.get('id_product_attribute', 0)):
            combination_binder = self.binder_for(
                'prestashop.product.combination')
            product = combination_binder.to_odoo(
                record['id_product_attribute'],
                unwrap=True)
            vals['product_id'] = product.id
        elif int(record.get('id_product', 0)):
            template = self.binder_for(
                'prestashop.product.template').to_odoo(
                    record['id_product'], unwrap=True)
            vals['product_tmpl_id'] = template.id
        return vals

    @mapping
    def pricelist_vals(self, record):
        vals = {}
        if float(record.get('price', 0)) > 0:
            vals = {
                'price_discount': -1,
                'price_surcharge': float(record['price'])
            }
        elif float(record.get('reduction', 0)) > 0:
            reduction_type = record.get('reduction_type')
            if reduction_type == 'percentage':
                vals = {
                    'price_discount': -1 * float(record['reduction'])
                }
            elif reduction_type == 'amount':
                vals = {
                    'price_surcharge': -1 * float(record['reduction'])
                }
        return vals

    @mapping
    def min_quantity(self, record):
        if int(record.get('from_quantity', 0)):
            return {'min_quantity': int(record['from_quantity'])}

    @mapping
    def sequence(self, record):
        return {'sequence': 5}

    @mapping
    def pricelist_version(self, record):
        if not self.backend_record.pricelist_id:
            raise exceptions.Warning(_(
                'Please configure a pricelist on prestashop backend'))
        return {
            'price_version_id':
            self.backend_record.pricelist_id.version_id[0].id
        }


@prestashop
class ProductPricelistItemImport(PrestashopImporter):
    """ Import one simple record """
    _model_name = 'prestashop.specific.price'

    def _has_to_skip(self):
        # Skip if has a global specific price Rule
        if int(self.prestashop_record.get('id_specific_price_rule', 0)):
            return True
        # Skip if pricelist item has from or to date
        default_no_date = '0000-00-00 00:00:00'
        if self.prestashop_record.get('from') != default_no_date or \
                self.prestashop_record.get('to') != default_no_date:
            return True
        # Skip import if one of the following vals are distinct to zero
        # because if we import the pricelist and the related product or
        # the pricelist item itself changes, the specific price in prestashop
        # will be overwritten with zero vals on this fields
        skip_no_zero_vals = [
            'id_shop',
            'id_shop_group',
            'id_country',
            'id_group',
            'id_customer',
            'id_currency',
            'id_cart']
        for skip_no_zero_val in skip_no_zero_vals:
            if int(self.prestashop_record.get(skip_no_zero_val, 0)) != 0:
                return True


@prestashop
class ProductPricelistItemBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.specific.price'
