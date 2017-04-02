# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector.queue.job import job
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.exporter import (
    PrestashopExporter
)
from openerp.addons.connector_prestashop.unit.mapper import (
    PrestashopExportMapper,
)
import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


class ExporterMixin(PrestashopExporter):

    def run(self, binding_id, *args, **kwargs):
        try:
            super(ExporterMixin, self).run(binding_id, **kwargs)
        except PrestaShopWebServiceError as error:
            self._handle_ws_error(binding_id, error, **kwargs)

    def _handle_ws_error(self, binding_id, error, **kwargs):
        binder = self.binder_for(self._model_name)
        manuf = binder.to_odoo(binding_id, unwrap=True)
        msg = _(
            'Export of %s failed. Error: %s.'
        ) % (self.msg_model_name, error.ps_error_msg)
        self.backend_record.add_checkpoint(
            model=manuf._name,
            record_id=manuf.id,
            message=msg,
        )


@prestashop
class ManufacturerExporter(ExporterMixin):
    _model_name = 'prestashop.manufacturer'
    msg_model_name = 'Manufacturer'

    def _export_addresses(self):
        partner_record = self.binding.odoo_id
        addresses = partner_record.child_ids or [partner_record, ]
        for address in addresses:
            self._export_dependency(
                address,
                'prestashop.manufacturer.address',
                bind_values={'prestashop_partner_id': self.binding.id},
                exporter_class=ManufacturerAddressExporter,
                force_sync=True)

    def _after_export(self):
        super(ManufacturerExporter, self)._export_dependencies()
        self._export_addresses()


@prestashop
class ManufacturerExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.manufacturer'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def active(self, record):
        return {'active': '1'}


@prestashop
class ManufacturerAddressExporter(ExporterMixin):
    _model_name = 'prestashop.manufacturer.address'
    msg_model_name = 'Manufacturer Address'


@prestashop
class AddressExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.manufacturer.address'
    direct = [
        # `alias` in PS is a label for the address and is required
        ('type', 'alias'),
        ('street', 'address1'),
        ('street2', 'address2'),
        ('city', 'city'),
        ('comment', 'other'),
        ('phone', 'phone'),
        ('mobile', 'phone_mobile'),
        ('zip', 'postcode'),
        # (m2o_to_backend('prestashop_partner_id'), 'id_manufacturer'),
    ]

    @mapping
    def name(self, record):
        # TODO: use partner 1st name last name module (?)
        partner = record.prestashop_partner_id
        parts = [
            x.strip().capitalize()
            for x in partner.display_name.split(' ') if x.strip()
        ]
        first = ' '.join(parts[:1])
        last = ' '.join(parts[1:]).strip() or first  # can't be null
        return {
            'firstname': first,
            'lastname': last,
        }

    @mapping
    def country(self, record):
        if record.country_id:
            binder = self.binder_for('prestashop.res.country')
            country_id = binder.to_backend(record.country_id.id, wrap=1)
            return {'id_country': country_id}
        return {}

    @mapping
    def manufacturer(self, record):
        binder = self.binder_for('prestashop.manufacturer')
        value = binder.to_backend(record.prestashop_partner_id.id)
        if value:
            return {'id_manufacturer': value}
        return {}


@job(default_channel='root.prestashop')
def export_manufacturer(session, partner_record_id, fields=None, **kwargs):
    """ Export supplier partner as manufacturer. """

    binding_model = 'prestashop.manufacturer'
    # get default backend
    backend = session.env['prestashop.backend'].search([], limit=1)
    env = backend.get_environment(binding_model, session=session)
    exporter = env.get_connector_unit(ManufacturerExporter)
    binding = exporter._get_or_create_binding(
        session.env['res.partner'].browse(partner_record_id),
        binding_model
    )
    return exporter.run(binding.id, fields, **kwargs)
