# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _
from openerp.addons.connector.unit.mapper import (
    ExportMapper,
    mapping,
    m2o_to_backend,
)
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.exporter import (
    PrestashopExporter
)
import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


class ExporterMixin(PrestashopExporter):

    def run(self, binding_id, **kwargs):
        try:
            super(ExporterMixin, self).run(binding_id, **kwargs)
        except PrestaShopWebServiceError as error:
            binder = self.binder_for('prestashop.manufacturer')
            manuf = binder.to_odoo(binding_id, unwrap=True)
            msg = _(
                'Import of %s `%s` '
                'with id `%s` failed. '
                'Error: `%s`'
            ) % (self.msg_model_name, manuf.name, manuf.id, error.ps_error_msg)
            self.backend_record.add_checkpoint(message=msg)


@prestashop
class ManufacturerExporter(ExporterMixin):
    _model_name = 'prestashop.manufacturer'
    msg_model_name = 'Manufacturer'


@prestashop
class ManufacturerExportMapper(ExportMapper):
    _model_name = 'prestashop.manufacturer'
    direct = [
        ('name', 'name'),
        ('active', 'active'),
    ]

    @mapping
    def associations(self, record):
        return {
            'associations': {
                'addresses': self._get_addresses(record),
            }
        }

    def _get_addresses(self, record):
        res = []
        binder = self.binder_for('prestashop.manufacturer.address')
        for item in record.child_ids:
            ext_id = binder.to_backend(item.id, wrap=True)
            if ext_id:
                res.append({'id': ext_id})
        return res


@prestashop
class ManufacturerAddressExporter(ExporterMixin):
    _model_name = 'prestashop.manufacturer.address'
    msg_model_name = 'Manufacturer Address'


@prestashop
class AddressExportMapper(ExportMapper):
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
        (m2o_to_backend('prestashop_partner_id'), 'id_manufacturer'),
    ]

    @mapping
    def name(self, record):
        # TODO: use partner 1st name last name module (?)
        partner = record.prestashop_partner_id
        parts = [
            x.strip() for x in partner.display_name.split(' ') if x.strip()
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
            country_id = binder.to_backend(record.country_id.id)
            return {'id_country': country_id}
        return {}
