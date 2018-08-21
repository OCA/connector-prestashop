# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields

from odoo.addons.connector.exception import MappingError
from odoo.addons.queue_job.job import job
from odoo.addons.connector.components.mapper import (
    mapping,
    only_create,
)
from ...components.importer import (
    import_batch,
)
from odoo.addons.component.core import Component


class RefundImporter(Component):
    _name = 'prestashop.refund.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.refund'

    _model_name = 'prestashop.refund'

    def _import_dependencies(self):
        record = self.prestashop_record
        self._import_dependency(
            record['id_customer'], 'prestashop.res.partner'
        )
        self._import_dependency(record['id_order'], 'prestashop.sale.order')

    def _open_refund(self, binding):
        invoice = binding.odoo_id
        if invoice.amount_total == float(self.prestashop_record['amount']):
            invoice.signal_workflow('invoice_open')
        else:
            self.backend_record.add_checkpoint(
                invoice, 
                message=_('The refund for order %s has a different amount '
                          'in PrestaShop and in Odoo.') % invoice.origin
            )

    def _after_import(self, binding):
        super(RefundImporter, self)._after_import(binding)
        self._open_refund(binding)


class RefundMapper(Component):
    _name = 'prestashop.refund.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.refund'
    _model_name = 'prestashop.refund'

    direct = [
        ('id', 'name'),
        ('date_add', 'date_invoice'),
    ]

    @mapping
    def journal(self, record):
        journal = self.backend_record.refund_journal_id
        if not journal:
            raise MappingError(
                _('The refund journal must be configured on '
                  'the PrestaShop Backend.')
            )
        return {'journal_id': journal.id}

    def _get_order(self, record):
        binder = self.binder_for('prestashop.sale.order')
        return binder.to_internal(record['id_order'])

    @mapping
    def from_sale_order(self, record):
        sale_order = self._get_order(record)
        fiscal_position = None
        if sale_order.fiscal_position_id:
            fiscal_position = sale_order.fiscal_position_id.id
        return {
            'origin': sale_order['name'],
            'fiscal_position_id': fiscal_position,
        }

    @mapping
    def comment(self, record):
        return {'comment': _('PrestaShop amount: %s') % record['amount']}

    @mapping
    @only_create
    def invoice_lines(self, record):
        slip_details = record.get(
            'associations', {}
        ).get('order_slip_details', []).get(
            self.backend_record.get_version_ps_key('order_slip_detail'), [])
        if isinstance(slip_details, dict):
            slip_details = [slip_details]
        lines = []
        order_binding = self._get_order(record)
        fpos = order_binding.fiscal_position_id
        shipping_line = self._invoice_line_shipping(record, fpos)
        if shipping_line:
            lines.append((0, 0, shipping_line))
        for slip_detail in slip_details:
            line = self._invoice_line(slip_detail, fpos)
            lines.append((0, 0, line))
        return {'invoice_line_ids': lines}

    def _invoice_line_shipping(self, record, fpos):
        order_line = self._get_shipping_order_line(record)
        if not order_line:
            return None
        if record['shipping_cost'] == '1':
            price_unit = order_line['price_unit']
        else:
            price_unit = record['shipping_cost_amount']
        if price_unit in [0.0, '0.00']:
            return None
        product = self.env['product.product'].browse(
            order_line['product_id'][0]
        )
        account_id = product.property_account_income_id.id
        if not account_id:
            account_id = product.categ_id.property_account_income_categ_id.id
        if fpos:
            fpos_obj = self.env['account.fiscal.position']
            account_id = fpos_obj.map_account(
                self.session.cr,
                self.session.uid,
                fpos,
                account_id
            )
        return {
            'quantity': 1,
            'product_id': product.id,
            'name': order_line['name'],
            'invoice_line_tax_id': [(6, 0, order_line['tax_id'])],
            'price_unit': price_unit,
            'discount': order_line['discount'],
            'account_id': account_id,
        }

    def _get_shipping_order_line(self, record):
        binder = self.binder_for('prestashop.sale.order')
        sale_order = binder.to_internal(record['id_order'], unwrap=True)
        if not sale_order.carrier_id:
            return None
        sale_order_line_ids = self.env['sale.order.line'].search([
            ('order_id', '=', sale_order.id),
            ('product_id', '=', sale_order.carrier_id.product_id.id),
        ])
        if not sale_order_line_ids:
            return None
        return sale_order_line_ids[0].read([])

    def _invoice_line(self, record, fpos):
        order_line = self._get_order_line(record['id_order_detail'])
        tax_ids = []
        if order_line is None:
            product_id = None
            name = "Order line not found"
            account_id = None
        else:
            product = order_line.product_id
            product_id = product.id
            name = order_line.name
            for tax in order_line.tax_id:
                tax_ids.append(tax.id)
            account_id = product.property_account_income_id.id
            if not account_id:
                categ = product.categ_id
                account_id = categ.property_account_income_categ_id.id
        if fpos and account_id:
            fpos_obj = self.session.pool['account.fiscal.position']
            account_id = fpos_obj.map_account(
                self.session.cr,
                self.session.uid,
                fpos,
                account_id
            )
        if record['product_quantity'] == '0':
            quantity = 1
        else:
            quantity = record['product_quantity']

        if self.backend_record.taxes_included:
            price_unit = record['amount_tax_incl']
        else:
            price_unit = record['amount_tax_excl']

        try:
            price_unit = float(price_unit) / float(quantity)
        except ValueError:
            pass

        discount = False
        if price_unit in ['0.00', ''] and order_line is not None:
            price_unit = order_line['price_unit']
            discount = order_line['discount']
        return {
            'quantity': quantity,
            'product_id': product_id,
            'name': name,
            'invoice_line_tax_id': [(6, 0, tax_ids)],
            'price_unit': price_unit,
            'discount': discount,
            'account_id': account_id,
        }

    def _get_order_line(self, order_details_id):
        order_line = self.env['prestashop.sale.order.line'].search([
            ('prestashop_id', '=', order_details_id),
            ('backend_id', '=', self.backend_record.id),
        ])
        if not order_line:
            return None
        return order_line.with_context(
            company_id=self.backend_record.company_id.id)

    @mapping
    def type(self, record):
        return {'type': 'out_refund'}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for('prestashop.res.partner')
        partner = binder.to_internal(record['id_customer'], unwrap=True)
        return {'partner_id': partner.id}

    @mapping
    def account_id(self, record):
        binder = self.binder_for('prestashop.res.partner')
        partner = binder.to_internal(record['id_customer'])
        partner = partner.with_context(
            company_id=self.backend_record.company_id.id,
        )
        return {'account_id': partner.property_account_receivable_id.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class RefundBatchImporter(Component):
    _name = 'prestashop.refund.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.refund'

    _model_name = 'prestashop.refund'
