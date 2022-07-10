# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import re

from odoo import fields, _
from odoo.addons.queue_job.job import job
from odoo.addons.connector.unit.mapper import (
    ImportMapper,
    mapping,
    only_create,
)
from ...components.importer import (
    PrestashopImporter,
    import_batch,
    DelayedBatchImporter,
)
# from ...backend import prestashop
# from odoo.addons.connector.unit.mapper import external_to_m2o

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping, external_to_m2o, only_create)


# # @prestashop
class PartnerImportMapper(Component):
    #_model_name = 'prestashop.res.partner'
    _name = 'prestashop.res.partner.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = ['prestashop.res.partner']

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('email', 'email'),
        ('newsletter', 'newsletter'),
        ('company', 'company'),
        ('active', 'active'),
        ('note', 'comment'),
        (external_to_m2o('id_shop_group'), 'shop_group_id'),
        (external_to_m2o('id_shop'), 'shop_id'),
        (external_to_m2o('id_default_group'), 'default_category_id'),
    ]

    @mapping
    def pricelist(self, record):
        binder = self.binder_for('prestashop.groups.pricelist')
        pricelist = binder.to_internal(record['id_default_group'], unwrap=True)
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
        parts = [record['firstname'], record['lastname']]
        name = ' '.join(p.strip() for p in parts if p.strip())
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
            partner_category_bindings |= binder.to_internal(group['id'])

        result = {'group_ids': [(6, 0, partner_category_bindings.ids)],
                  'category_id': [(4, b.openerp_id.id)
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
            erp_lang = binder.to_internal(record['id_lang'])
        if not erp_lang:
            erp_lang = self.env.ref('base.lang_en')
        return {'lang': erp_lang.code}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


# # @prestashop
class ResPartnerImporter(Component):
    #_model_name = 'prestashop.res.partner'
    _name = 'prestashop.res.partner.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.res.partner']



    def _import_dependencies(self):
        groups = self.prestashop_record.get('associations', {}) \
            .get('groups', {}).get(
            self.backend_record.get_version_ps_key('group'), [])
        if not isinstance(groups, list):
            groups = [groups]
        for group in groups:
            self._import_dependency(group['id'],
                                    'prestashop.res.partner.category')

    def _after_import(self, binding):
        super(ResPartnerImporter, self)._after_import(binding)
        binder = self.binder_for()
        ps_id = binder.to_external(binding)
        self.env['prestashop.address'].with_delay(priority=10).import_batch(
            backend=self.backend_record,
            filters={'filter[id_customer]': '%d' % (ps_id,)})


# # @prestashop
class PartnerBatchImporter(Component):
#     _model_name = 'prestashop.res.partner'
    _name = 'prestashop.res.partner.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.res.partner']



# # @prestashop
class AddressImportMapper(Component):
    #_model_name = 'prestashop.address'
    _name = 'prestashop.address.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = ['prestashop.address']


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
        (external_to_m2o('id_customer'), 'prestashop_partner_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        binder = self.binder_for('prestashop.res.partner')
        parent = binder.to_internal(record['id_customer'], unwrap=True)
        return {'parent_id': parent.id}

    @mapping
    def name(self, record):
        parts = [record['firstname'], record['lastname']]
        if record['alias']:
            parts.append('(%s)' % record['alias'])
        name = ' '.join(p.strip() for p in parts if p.strip())
        return {'name': name}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def country(self, record):
        if record.get('id_country'):
            binder = self.binder_for('prestashop.res.country')
            country = binder.to_internal(record['id_country'], unwrap=True)
            return {'country_id': country.id}
        return {}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @only_create
    @mapping
    def type(self, record):
        # do not set 'contact', otherwise the address fields are shared with
        # the parent
        return {'type': 'other'}


# # @prestashop
class AddressImporter(Component):
#    _model_name = 'prestashop.address'
    _name = 'prestashop.address.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.address']



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
                msg = _('Please, check the VAT number: %s') % vat_number
                self.backend_record.add_checkpoint(
                    model=binding.parent_id._name,
                    record_id=binding.parent_id.id,
                    message=msg,
                )


# # @prestashop
class AddressBatchImporter(Component):
    #_model_name = 'prestashop.address'
    _name = 'prestashop.address.mapper'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.address']



@job(default_channel='root.prestashop')
def import_customers_since(env, since_date=None, **kwargs):
    """ Prepare the import of partners modified on PrestaShop """
    filters = None
    if since_date:
        filters = {
            'date': '1',
            'filter[date_upd]': '>[%s]' % since_date}
    now_fmt = fields.Datetime.now()
    result = import_batch(env, filters, **kwargs) or ''
    result += import_batch(env, filters, priority=15, **kwargs) or ''
    env.backend_record.import_partners_since = now_fmt
    # env['prestashop.backend'].browse(backend_id).write({
    #     'import_partners_since': now_fmt,
    # })
    return result
