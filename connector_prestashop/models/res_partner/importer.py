# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import re
from datetime import datetime

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import (
    ImportMapper,
    mapping,
)
from ...unit.importer import (
    PrestashopImporter,
    import_batch,
    DelayedBatchImporter,
)
from ...backend import prestashop
from ...unit.mapper import backend_to_m2o
from ...connector import add_checkpoint

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


@prestashop
class PartnerImportMapper(ImportMapper):
    _model_name = 'prestashop.res.partner'

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('email', 'email'),
        ('newsletter', 'newsletter'),
        ('company', 'company'),
        ('active', 'active'),
        ('note', 'comment'),
        (backend_to_m2o('id_shop_group'), 'shop_group_id'),
        (backend_to_m2o('id_shop'), 'shop_id'),
        (backend_to_m2o('id_default_group'), 'default_category_id'),
    ]

    @mapping
    def pricelist(self, record):
        binder = self.binder_for('prestashop.groups.pricelist')
        pricelist = binder.to_odoo(
            record['id_default_group'], unwrap=True)
        if not pricelist:
            return {}
        return {'property_product_pricelist': pricelist.id}

    @mapping
    def birthday(self, record):
        if record['birthday'] in ['0000-00-00', '']:
            return {}
        return {'birthday': record['birthday']}

    @mapping
    def name(self, record):
        name = ""
        if record['firstname']:
            name += record['firstname']
        if record['lastname']:
            if len(name) != 0:
                name += " "
            name += record['lastname']
        return {'name': name}

    @mapping
    def groups(self, record):
        groups = record.get(
            'associations', {}).get('groups', {}).get(
            self.backend_record.get_version_ps_key('group'), [])
        if not isinstance(groups, list):
            groups = [groups]
        model_name = 'prestashop.res.partner.category'
        partner_category_bindings = self.env[model_name].browse()
        binder = self.binder_for(model_name)
        for group in groups:
            partner_category_bindings |= binder.to_odoo(group['id'])

        result = {'group_ids': [(6, 0, partner_category_bindings.ids)],
                  'category_id': [(4, b.odoo_id.id)
                                  for b in partner_category_bindings]}
        return result

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def lang(self, record):
        binder = self.binder_for('prestashop.res.lang')
        erp_lang = None
        if record.get('id_lang'):
            erp_lang = binder.to_odoo(record['id_lang'])
        if erp_lang is None:
            erp_lang = self.env.ref('base.lang_en')
        model = self.session.env['prestashop.res.lang']
        erp_lang = model.search([('id', '=', erp_lang.id)], limit=1)
        return {'lang': erp_lang.code}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def is_company(self, record):
        # This is sad because we _have_ to have a company partner if we want to
        # store multiple adresses... but... well... we have customers who want
        # to be billed at home and be delivered at work... (...)...
        return {'is_company': True}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


@prestashop
class ResPartnerRecordImport(PrestashopImporter):
    _model_name = 'prestashop.res.partner'

    def _import_dependencies(self):
        groups = self.prestashop_record.get('associations', {}) \
            .get('groups', {}).get(
            self.backend_record.get_version_ps_key('group'), [])
        if not isinstance(groups, list):
            groups = [groups]
        for group in groups:
            self._import_dependency(
                group['id'], 'prestashop.res.partner.category')

    def _after_import(self, erp_id):
        binder = self.binder_for(self._model_name)
        ps_id = binder.to_backend(erp_id)
        import_batch.delay(
            self.session,
            'prestashop.address',
            self.backend_record.id,
            filters={'filter[id_customer]': '%d' % (ps_id)},
            priority=10,
        )


@prestashop
class PartnerBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.res.partner'


@prestashop
class AddressImportMapper(ImportMapper):
    _model_name = 'prestashop.address'

    direct = [
        ('address1', 'street'),
        ('address2', 'street2'),
        ('city', 'city'),
        ('other', 'comment'),
        ('phone', 'phone'),
        ('phone_mobile', 'mobile'),
        ('postcode', 'zip'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        (backend_to_m2o('id_customer'), 'prestashop_partner_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def partner_type(self, record):
        return {'type': 'delivery'}

    @mapping
    def parent_id(self, record):
        parent = self.binder_for('prestashop.res.partner').to_odoo(
            record['id_customer'], unwrap=True)
        if record['vat_number']:
            vat_number = record['vat_number'].replace('.', '').replace(' ', '')
            # TODO: move to custom module
            regexp = re.compile('^[a-zA-Z]{2}')
            if not regexp.match(vat_number):
                vat_number = 'ES' + vat_number
            if self._check_vat(vat_number):
                parent.write({'vat': vat_number})
            else:
                add_checkpoint(
                    self.session,
                    'res.partner',
                    parent.id,
                    self.backend_record.id
                )
        return {'parent_id': parent.id}

    # TODO move to custom localization module
    @mapping
    def dni(self, record):
        parent = self.binder_for('prestashop.res.partner').to_odoo(
            record['id_customer'], unwrap=True)
        if not record['vat_number'] and record.get('dni'):
            vat_number = record['dni'].replace('.', '').replace(
                ' ', '').replace('-', '')
            regexp = re.compile('^[a-zA-Z]{2}')
            if not regexp.match(vat_number):
                vat_number = 'ES' + vat_number
            if self._check_vat(vat_number):
                parent.write({'vat': vat_number})
            else:
                add_checkpoint(
                    self.session,
                    'res.partner',
                    parent.id,
                    self.backend_record.id
                )
        return {'parent_id': parent.id}

    def _check_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:]
        return self.env['res.partner'].simple_vat_check(
            vat_country,
            vat_number,
        )

    @mapping
    def name(self, record):
        name = ""
        if record['firstname']:
            name += record['firstname']
        if record['lastname']:
            if name:
                name += " "
            name += record['lastname']
        if record['alias']:
            if name:
                name += " "
            name += '('+record['alias']+')'
        return {'name': name}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def country(self, record):
        if record.get('id_country'):
            binder = self.binder_for('prestashop.res.country')
            erp_country = binder.to_odoo(
                record['id_country'], unwrap=True)
            return {'country_id': erp_country.id}
        return {}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


@prestashop
class AddressImporter(PrestashopImporter):
    _model_name = 'prestashop.address'

    def _check_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:]
        partner_model = self.env['res.partner']
        return partner_model.simple_vat_check(vat_country, vat_number)

    def _after_import(self, binding):
        record = self.prestashop_record
        vat_number = None
        if record['vat_number']:
            vat_number = record['vat_number'].replace('.', '').replace(' ', '')
        # TODO move to custom localization module
        elif not record['vat_number'] and record.get('dni'):
            vat_number = record['dni'].replace('.', '').replace(
                ' ', '').replace('-', '')
        if vat_number:
            # TODO: move to custom module
            regexp = re.compile('^[a-zA-Z]{2}')
            if not regexp.match(vat_number):
                vat_number = 'ES' + vat_number
            if self._check_vat(vat_number):
                binding.parent_id.write({'vat': vat_number})
            else:
                add_checkpoint(
                    self.session,
                    'res.partner',
                    binding.parent_id.id,
                    self.backend_record.id
                )


@prestashop
class AddressBatchImporter(DelayedBatchImporter):
    _model_name = 'prestashop.address'


@job(default_channel='root.prestashop')
def import_customers_since(session, backend_id, since_date=None):
    """ Prepare the import of partners modified on PrestaShop """
    filters = None
    if since_date:
        filters = {
            'date': '1',
            'filter[date_upd]': '>[%s]' % (since_date)}
    now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    import_batch(
        session, 'prestashop.res.partner.category', backend_id, filters
    )
    import_batch(
        session, 'prestashop.res.partner', backend_id, filters, priority=15
    )

    session.env['prestashop.backend'].browse(backend_id).write({
        'import_partners_since': now_fmt,
    })
