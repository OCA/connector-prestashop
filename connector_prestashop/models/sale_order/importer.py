# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from datetime import datetime, timedelta
from decimal import Decimal

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.exception import FailedJobError, NothingToDoJob
from openerp.addons.connector.unit.mapper import ImportMapper, mapping
from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange,
)
from ...unit.backend_adapter import GenericAdapter
from ...unit.importer import (
    PrestashopImporter,
    import_batch,
    DelayedBatchImporter,
)
from ...unit.exception import OrderImportRuleRetry
from ...backend import prestashop

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug('Can not `from prestapyt import PrestaShopWebServiceError`.')


@prestashop
class PrestaShopSaleOrderOnChange(SaleOrderOnChange):
    _model_name = 'prestashop.sale.order'


@prestashop
class SaleImportRule(ConnectorUnit):
    _model_name = ['prestashop.sale.order']

    def _rule_always(self, record, method):
        """ Always import the order """
        return True

    def _rule_never(self, record, method):
        """ Never import the order """
        raise NothingToDoJob('Orders with payment method %s '
                             'are never imported.' %
                             record['payment']['method'])

    def _rule_paid(self, record, method):
        """ Import the order only if it has received a payment """
        if self._get_paid_amount(record) == 0.0:
            raise OrderImportRuleRetry('The order has not been paid.\n'
                                       'The import will be retried later.')

    def _get_paid_amount(self, record):
        payment_adapter = self.unit_for(
            GenericAdapter,
            '__not_exist_prestashop.payment'
        )
        payment_ids = payment_adapter.search({
            'filter[order_reference]': record['reference']
        })
        paid_amount = 0.0
        for payment_id in payment_ids:
            payment = payment_adapter.read(payment_id)
            paid_amount += float(payment['amount'])
        return paid_amount

    _rules = {
        'always': _rule_always,
        'paid': _rule_paid,
        'authorized': _rule_paid,
        'never': _rule_never,
    }

    def check(self, record):
        """ Check whether the current sale order should be imported
        or not. It will actually use the payment method configuration
        and see if the chosen rule is fullfilled.

        :returns: True if the sale order should be imported
        :rtype: boolean
        """
        session = self.session
        payment_method = record['payment']
        method = session.env['payment.method'].search(
            [('name', '=', payment_method)])
        if not method:
            raise FailedJobError(
                "The configuration is missing for the Payment Method '%s'.\n\n"
                "Resolution:\n"
                "- Go to 'Sales > Configuration > Sales > Customer Payment "
                "Method'\n"
                "- Create a new Payment Method with name '%s'\n"
                "-Eventually  link the Payment Method to an existing Workflow "
                "Process or create a new one." % (payment_method,
                                                  payment_method))
        self._rule_global(record, method)
        self._rules[method.import_rule](self, record, method)

    def _rule_global(self, record, method):
        """ Rule always executed, whichever is the selected rule """
        order_id = record['id']
        max_days = method.days_before_cancel
        if not max_days:
            return
        if self._get_paid_amount(record) != 0.0:
            return
        fmt = '%Y-%m-%d %H:%M:%S'
        order_date = datetime.strptime(record['date_add'], fmt)
        if order_date + timedelta(days=max_days) < datetime.now():
            raise NothingToDoJob('Import of the order %s canceled '
                                 'because it has not been paid since %d '
                                 'days' % (order_id, max_days))


@prestashop
class SaleOrderMapper(ImportMapper):
    _model_name = 'prestashop.sale.order'

    direct = [
        ('date_add', 'date_order'),
        ('invoice_number', 'prestashop_invoice_number'),
        ('delivery_number', 'prestashop_delivery_number'),
        ('total_paid', 'total_amount'),
        ('total_shipping_tax_incl', 'total_shipping_tax_included'),
        ('total_shipping_tax_excl', 'total_shipping_tax_excluded')
    ]

    def _get_sale_order_lines(self, record):
        orders = record['associations'].get(
            'order_rows', {}).get(
            self.backend_record.get_version_ps_key('order_row'), [])
        if isinstance(orders, dict):
            return [orders]
        return orders

    def _get_discounts_lines(self, record):
        if record['total_discounts'] == '0.00':
            return []
        adapter = self.unit_for(
            GenericAdapter, 'prestashop.sale.order.line.discount')
        discount_ids = adapter.search({'filter[id_order]': record['id']})
        discount_mappers = []
        for discount_id in discount_ids:
            discount_mappers.append({'id': discount_id})
        return discount_mappers

    children = [
        (_get_sale_order_lines,
         'prestashop_order_line_ids', 'prestashop.sale.order.line'),
        (_get_discounts_lines,
         'prestashop_discount_line_ids', 'prestashop.sale.order.line.discount')
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        # TODO patch ImportMapper in connector to support callable
        if callable(from_attr):
            child_records = from_attr(self, source)
        else:
            child_records = source[from_attr]

        children = []
        for child_record in child_records:
            adapter = self.unit_for(GenericAdapter, model_name)
            detail_record = adapter.read(child_record['id'])

            mapper = self._get_map_child_unit(model_name)
            items = mapper.get_items(
                [detail_record], map_record, to_attr, options=self.options
            )
            children.extend(items)
        return children

    def _sale_order_exists(self, name):
        sale_order = self.env['sale.order'].search([
            ('name', '=', name),
            ('company_id', '=', self.backend_record.company_id.id),
        ], limit=1)
        return len(sale_order) == 1

    @mapping
    def name(self, record):
        basename = record['reference']
        if not self._sale_order_exists(basename):
            return {"name": basename}
        i = 1
        name = basename + '_%d' % (i)
        while self._sale_order_exists(name):
            i += 1
            name = basename + '_%d' % (i)
        return {"name": name}

    @mapping
    def partner_id(self, record):
        partner = self.binder_for('prestashop.res.partner').to_odoo(
            record['id_customer'], unwrap=True)
        return {'partner_id': partner.id}

    @mapping
    def partner_invoice_id(self, record):
        address = self.binder_for('prestashop.address').to_odoo(
            record['id_address_invoice'], unwrap=True)
        return {'partner_invoice_id': address.id}

    @mapping
    def partner_shipping_id(self, record):
        shipping = self.binder_for('prestashop.address').to_odoo(
            record['id_address_delivery'], unwrap=True)
        return {'partner_shipping_id': shipping.id}

    @mapping
    def pricelist_id(self, record):
        return {'pricelist_id': 1}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def payment(self, record):
        method = self.env['payment.method'].search([
            ('name', '=', record['payment']),
            ('company_id', '=', self.backend_record.company_id.id),
        ], limit=1)
        assert method, ("Payment method '%s' has not been found ; "
                        "you should create it manually (in Sales->"
                        "Configuration->Sales->Payment Methods" %
                        record['payment'])
        return {'payment_method_id': method.id}

    @mapping
    def carrier_id(self, record):
        if record['id_carrier'] == '0':
            return {}
        carrier = self.binder_for('prestashop.delivery.carrier').to_odoo(
            record['id_carrier'], unwrap=True)
        return {'carrier_id': carrier.id}

    @mapping
    def total_tax_amount(self, record):
        tax = (float(record['total_paid_tax_incl']) -
               float(record['total_paid_tax_excl']))
        return {'total_amount_tax': tax}


@prestashop
class SaleOrderImport(PrestashopImporter):
    _model_name = ['prestashop.sale.order']

    def _import_dependencies(self):
        record = self.prestashop_record
        self._import_dependency(
            record['id_customer'], 'prestashop.res.partner')
        self._import_dependency(
            record['id_address_invoice'], 'prestashop.address'
        )
        self._import_dependency(
            record['id_address_delivery'], 'prestashop.address'
        )

        if record['id_carrier'] != '0':
            self._import_dependency(
                record['id_carrier'], 'prestashop.delivery.carrier')

        orders = record['associations'] \
            .get('order_rows', {}) \
            .get(self.backend_record.get_version_ps_key('order_row'), [])
        if isinstance(orders, dict):
            orders = [orders]
        for order in orders:
            try:
                self._import_dependency(
                    order['product_id'], 'prestashop.product.template')
            except PrestaShopWebServiceError:
                pass

    def _after_import(self, erp_id):
        erp_order = erp_id
        shipping_total = erp_order.total_shipping_tax_included \
            if self.backend_record.taxes_included \
            else erp_order.total_shipping_tax_excluded
        if shipping_total:
            sale_line_obj = self.session.env['sale.order.line']
            sale_line_obj.create({
                'order_id': erp_order.odoo_id.id,
                'product_id':
                    erp_order.odoo_id.carrier_id.product_id.id,
                'price_unit':  shipping_total,
                'is_delivery': True
            })
        erp_order.odoo_id.recompute()
        return True

    def _check_refunds(self, id_customer, id_order):
        backend_adapter = self.unit_for(
            GenericAdapter, 'prestashop.refund'
        )
        filters = {'filter[id_customer]': id_customer}
        refund_ids = backend_adapter.search(filters=filters)
        for refund_id in refund_ids:
            refund = backend_adapter.read(refund_id)
            if refund['id_order'] == id_order:
                continue
            self._import_dependency(refund_id, 'prestashop.refund')

    def _has_to_skip(self):
        """ Return True if the import can be skipped """
        if self._get_binding():
            return True
        rules = self.unit_for(SaleImportRule)
        return rules.check(self.prestashop_record)


@prestashop
class SaleOrderBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.sale.order'


@prestashop
class SaleOrderLineMapper(ImportMapper):
    _model_name = 'prestashop.sale.order.line'

    direct = [
        ('product_name', 'name'),
        ('id', 'sequence'),
        ('product_quantity', 'product_uom_qty'),
        ('reduction_percent', 'discount'),
    ]

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}

    def none_product(self, record):
        product_id = True
        if 'product_attribute_id' not in record:
            template = self.binder_for(
                'prestashop.product.template').to_odoo(
                    record['product_id'], unwrap=True)
            product_id = self.env['product.product'].search([
                ('product_tmpl_id', '=', template.id),
                ('company_id', '=', self.backend_record.company_id.id)])
        return not product_id

    @mapping
    def price_unit(self, record):
        if self.backend_record.taxes_included:
            key = 'unit_price_tax_incl'
        else:
            key = 'unit_price_tax_excl'
        if record['reduction_percent']:
            reduction = Decimal(record['reduction_percent'])
            price = Decimal(record[key])
            price_unit = price / ((100 - reduction) / 100)
        else:
            price_unit = record[key]
        return {'price_unit': price_unit}

    @mapping
    def product_id(self, record):
        if int(record.get('product_attribute_id', 0)):
            combination_binder = self.binder_for(
                'prestashop.product.combination')
            product = combination_binder.to_odoo(
                record['product_attribute_id'],
                unwrap=True)
        else:
            template = self.binder_for(
                'prestashop.product.template').to_odoo(
                    record['product_id'], unwrap=True)
            product = self.env['product.product'].search([
                ('product_tmpl_id', '=', template.id),
                ('company_id', '=', self.backend_record.company_id.id)],
                limit=1,
            )
            if product is None:
                return self.tax_id(record)
        return {'product_id': product.id}

    def _find_tax(self, ps_tax_id):
        binder = self.binder_for('prestashop.account.tax')
        oe_tax = binder.to_odoo(ps_tax_id, unwrap=True)
        return oe_tax.id

    @mapping
    def tax_id(self, record):
        taxes = record.get('associations', {}).get('taxes', {}).get(
            self.backend_record.get_version_ps_key('tax'), [])
        if not isinstance(taxes, list):
            taxes = [taxes]
        result = []
        for tax in taxes:
            odoo_id = self._find_tax(tax['id'])
            if odoo_id:
                result.append(odoo_id)
        if result:
            return {'tax_id': [(6, 0, result)]}
        return {}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class SaleOrderLineRecordImport(PrestashopImporter):
    _model_name = [
        'prestashop.sale.order.line',
    ]

    def run(self, prestashop_record, order_id):
        """ Run the synchronization

        :param prestashop_record: record from PrestaShop sale order
        """
        self.prestashop_record = prestashop_record

        skip = self._has_to_skip()
        if skip:
            return skip

        # import the missing linked resources
        self._import_dependencies()

        map_record = self.mapper.map_record(self.prestashop_record)
        record = map_record.values(for_create=True)
        record.order_id = order_id

        # special check on data before import
        self._validate_data(record)

        erp_id = self._create(record)
        self._after_import(erp_id)


@prestashop
class SaleOrderLineDiscount(ImportMapper):
    _model_name = 'prestashop.sale.order.line.discount'

    direct = []

    @mapping
    def discount(self, record):
        return {
            'name': record['name'],
            'product_uom_qty': 1,
        }

    @mapping
    def price_unit(self, record):
        if self.backend_record.taxes_included:
            price_unit = record['value']
        else:
            price_unit = record['value_tax_excl']
        if price_unit[0] != '-':
            price_unit = '-' + price_unit
        return {'price_unit': price_unit}

    @mapping
    def product_id(self, record):
        if self.backend_record.discount_product_id:
            return {'product_id': self.backend_record.discount_product_id.id}
        product_discount = self.session.env.ref(
            'connector_ecommerce.product_product_discount')
        return {'product_id': product_discount.id}

    @mapping
    def tax_id(self, record):
        return {'tax_id': [
            (6, 0, self.backend_record.discount_product_id.taxes_id.ids)
        ]}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}


@job(default_channel='root.prestashop')
def import_orders_since(session, backend_id, since_date=None):
    """ Prepare the import of orders modified on PrestaShop """
    filters = None
    if since_date:
        filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
    import_batch(
        session,
        'prestashop.sale.order',
        backend_id,
        filters,
        priority=10,
        max_retries=0
    )
    if since_date:
        filters = {'date': '1', 'filter[date_add]': '>[%s]' % since_date}
    try:
        import_batch(session, 'prestashop.mail.message', backend_id, filters)
    except:
        pass

    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    session.env['prestashop.backend'].browse(backend_id).write({
        'import_orders_since': now_fmt
    })
