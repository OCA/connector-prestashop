# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models

from odoo.addons.connector.exception import RetryableJobError


class PrestashopBinding(models.AbstractModel):
    _name = "prestashop.binding"
    _inherit = "external.binding"
    _description = "PrestaShop Binding (abstract)"

    # 'odoo_id': odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name="prestashop.backend",
        string="PrestaShop Backend",
        required=True,
        ondelete="restrict",
    )
    active = fields.Boolean(string="Active", default=True)
    prestashop_id = fields.Integer("ID on PrestaShop")
    no_export = fields.Boolean("No export to PrestaShop")

    _sql_constraints = [
        (
            "prestashop_uniq",
            "unique(backend_id, prestashop_id)",
            "A record with same ID on PrestaShop already exists.",
        ),
    ]

    def check_active(self, backend):
        if not backend.active:
            raise RetryableJobError(
                "Backend %s is inactive please consider changing this"
                "The job will be retried later." % (backend.name,)
            )

    @api.model
    def import_record(self, backend, prestashop_id, force=False):
        """Import a record from PrestaShop"""
        self.check_active(backend)
        with backend.work_on(self._name) as work:
            importer = work.component(usage="record.importer")
            return importer.run(prestashop_id, force=force)

    @api.model
    def import_batch(self, backend, filters=None, **kwargs):
        """Prepare a batch import of records from PrestaShop"""
        self.check_active(backend)
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage="batch.importer")
            return importer.run(filters=filters, **kwargs)

    def export_record(self, fields=None):
        """Export a record on PrestaShop"""
        self.ensure_one()
        self.check_active(self.backend_id)
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage="record.exporter")
            return exporter.run(self, fields)

    def export_delete_record(self, backend, external_id, attributes=None):
        """Delete a record on PrestaShop"""
        self.check_active(backend)
        with backend.work_on(self._name) as work:
            deleter = work.component(usage="record.exporter.deleter")
            return deleter.run(external_id, attributes)

    # TODO: Research
    def resync(self):
        func = self.import_record
        if self.env.context.get("connector_delay"):
            func = self.with_delay(priority=5).import_record
        for record in self:
            func(record.backend_id, record.prestashop_id)
        return True


class PrestashopBindingOdoo(models.AbstractModel):
    _name = "prestashop.binding.odoo"
    _inherit = "prestashop.binding"
    _description = "PrestaShop Binding with Odoo binding (abstract)"

    def _get_selection(self):
        records = self.env["ir.model"].search([])
        return [(r.model, r.name) for r in records] + [("", "")]

    # 'odoo_id': odoo-side id must be re-declared in concrete model
    # for having a many2one instead of a reference field
    odoo_id = fields.Reference(
        required=True,
        ondelete="cascade",
        string="Odoo binding",
        selection=_get_selection,
    )

    _sql_constraints = [
        (
            "prestashop_erp_uniq",
            "unique(backend_id, odoo_id)",
            "An ERP record with same ID already exists on PrestaShop.",
        ),
    ]
