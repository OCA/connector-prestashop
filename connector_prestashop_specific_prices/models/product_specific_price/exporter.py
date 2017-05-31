# -*- coding: utf-8 -*-
# © 2017 FactorLibre - Kiko Peiro <francisco.peiro@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import exceptions, _
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.exporter import \
    PrestashopExporter
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_write
from openerp.addons.connector_prestashop.unit.mapper import \
    PrestashopExportMapper
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector_prestashop.unit.exporter import export_record


@on_record_write(model_names='product.pricelist.item')
def prestashop_specific_price_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    specific_price_obj = session.env['prestashop.specific.price']
    specific_price_ext_ids = specific_price_obj.search([
        ('odoo_id', '=', record_id),
    ])
    for price_id in specific_price_ext_ids:
        export_record.delay(
            session,
            'prestashop.specific.price',
            price_id.id, priority=50)


@prestashop
class ProductPricelistExport(PrestashopExporter):
    _model_name = 'prestashop.specific.price'

    def _create(self, data):
        res = super(ProductPricelistExport, self)._create(data)
        return res['prestashop']['specific_price']['id']


@prestashop
class ProductPricelistExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.specific.price'

    @mapping
    def min_quantity(self, record):
        return {'from_quantity': record.min_quantity or 1}

    @mapping
    def product_id(self, record):
        binder = self.binder_for('prestashop.product.template')
        product_tmpl_id = record.product_tmpl_id.id or \
            record.product_id.product_tmpl_id.id
        ext_product_tmpl_id = binder.to_backend(product_tmpl_id, wrap=True)
        return {'id_product': ext_product_tmpl_id}

    @mapping
    def product_attribute_id(self, record):
        binder = self.binder_for('prestashop.product.combination')
        if record.product_id:
            ext_product_id = binder.to_backend(record.product_id.id, wrap=True)
            return {'id_product_attribute': ext_product_id}

    @mapping
    def default_values(self, record):
        return {
            'id_shop': '0',
            'id_shop_group': '0',
            'id_country': '0',
            'id_group': '0',
            'id_customer': '0',
            'id_currency': '0',
            'id_cart': '0',
            'from': '0000-00-00 00:00:00',
            'to': '0000-00-00 00:00:00'
        }

    @mapping
    def pricelist_vals(self, record):
        dp_obj = self.env['decimal.precision']
        precision = dp_obj.precision_get('Product Price')
        vals = {
            'price': '-1',
            'reduction': 0,
            'reduction_type': 'amount'
        }
        if record.price_discount == -1:
            if record.price_surcharge > 0:
                vals['price'] = round(record.price_surcharge, precision)
        elif record.price_discount == 0 and record.price_surcharge < 0:
            vals.update({
                'reduction': round(abs(record.price_surcharge), precision),
                'reduction_type': 'amount'})
        elif record.price_discount < 0 and record.price_surcharge == 0:
            vals.update({
                'reduction': abs(record.price_discount),
                'reduction_type': 'percentage'}
            )
        return vals


@job(default_channel='root.prestashop')
def export_specific_prices_to_backend(session, backend_id):
    """ Prepare the export of specific prices to PrestaShop """
    pricelist_item_env = session.env['product.pricelist.item']
    specific_price_env = session.env['prestashop.specific.price']

    backend_record = session.env['prestashop.backend'].browse(backend_id)
    if not backend_record.pricelist_id:
        raise exceptions.Warning(_(
            'Please configure a pricelist on prestashop backend'))
    pricelist_version_ids = backend_record.pricelist_id.version_id.ids
    pricelist_item_ids = []
    tmpl_items = pricelist_item_env.search([
        ('price_version_id', 'in', pricelist_version_ids),
        ('product_tmpl_id.prestashop_bind_ids.backend_id', '=',
         backend_record.id),
        ('product_id', '=', False)
    ])
    pricelist_item_ids += tmpl_items.ids
    prod_items = pricelist_item_env.search([
        ('price_version_id', 'in', pricelist_version_ids),
        ('product_id.prestashop_bind_ids.backend_id', '=',
         backend_record.id),
    ])
    pricelist_item_ids += prod_items.ids
    for item_id in pricelist_item_ids:
        specific_price_ext = specific_price_env.search([
            ('backend_id', '=', backend_record.id),
            ('odoo_id', '=', item_id),
        ], limit=1)
        if not specific_price_ext:
            specific_price_ext = specific_price_env.with_context(
                connector_no_export=True).create({
                    'backend_id': backend_record.id,
                    'odoo_id': item_id,
                })
        export_record.delay(
            session,
            'prestashop.specific.price',
            specific_price_ext.id, priority=15)
