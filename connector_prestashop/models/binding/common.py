# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

from openerp.addons.connector.session import ConnectorSession
from ...unit.importer import import_record


class PrestashopBinding(models.AbstractModel):
    _name = 'prestashop.binding'
    _inherit = 'external.binding'
    _description = 'PrestaShop Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        required=True,
        ondelete='restrict'
    )
    prestashop_id = fields.Integer('ID on PrestaShop')

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A record with same ID already exists on PrestaShop.'),
    ]

    @api.multi
    def resync(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        func = import_record
        if self.env.context and self.env.context.get('connector_delay'):
            func = import_record.delay
        for record in self:
            func(session, self._name, record.backend_id.id,
                 record.prestashop_id)
        return True


class PrestashopBindingOdoo(models.AbstractModel):
    _name = 'prestashop.binding.odoo'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Binding with Odoo binding (abstract)'

    def _get_selection(self):
        records = self.env['ir.model'].search([])
        return [(r.model, r.name) for r in records] + [('', '')]

    # 'odoo_id': odoo-side id must be re-declared in concrete model
    # for having a many2one instead of a reference field
    odoo_id = fields.Reference(
        required=True,
        ondelete='cascade',
        string='Odoo binding',
        selection=_get_selection,
    )

    _sql_constraints = [
        ('prestashop_erp_uniq', 'unique(backend_id, odoo_id)',
         'An ERP record with same ID already exists on PrestaShop.'),
    ]
