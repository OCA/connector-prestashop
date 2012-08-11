# -*- encoding: utf-8 -*-
###############################################################################
#
#   Prestashop_catalog_manager for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>. All Rights Reserved
#   @author : Sébastien BEAU <sebastien.beau@akretion.com>
#             Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


from osv import osv, fields
from base_external_referentials.decorator import only_for_referential

class product_attribute(osv.osv):
    _inherit = 'product.attribute'

    _columns = {
        'presta_position': fields.integer('Prestashop Position'),
        'external_referential_ids': fields.many2many('external.referential', 'ext_product_attributes', 'attribute_id', 'referential_id', 'External Referentials'),
    }

    def _get_last_exported_date(self, cr, uid, external_session, context=None):
        return external_session.referential_id.last_product_attributes_export_date

    def _set_last_exported_date(self, cr, uid, external_session, date, context=None):
        return external_session.referential_id.write({'last_product_attributes_export_date': date})

    @only_for_referential('prestashop')
    def get_ids_and_update_date(self, cr, uid, external_session, ids=None, last_exported_date=None, context=None):
        referential_ids = []
        for attribute in external_session.referential_id.product_attribute_ids:
            referential_ids.append(attribute.id)
        if ids:
            ids = list(set(ids).intersection(set(referential_ids)))
        else:
            ids = referential_ids
        return super(product_attribute, self).get_ids_and_update_date(cr, uid, external_session, ids=ids, last_exported_date=last_exported_date, context=context)

    @only_for_referential('prestashop')
    def _transform_and_send_one_resource(self, cr, uid, external_session, resource, resource_id,
                            update_date, mapping, mapping_id, defaults=None, context=None):
        option_ids = resource['no_lang']['option_ids']
        res = super(product_attribute, self)._transform_and_send_one_resource(cr, uid, external_session, 
resource, resource_id, update_date, mapping, mapping_id, defaults=defaults, context=context)
        for option_id in option_ids:
            self.pool.get('attribute.option')._export_one_resource(cr, uid, external_session, option_id, context=context)
        return res

    def create(self, cr, uid, vals, context=None):
        if not context.get('dont_add_referentials'):
            prestashop_type_id = self.pool.get('external.referential.type').search(cr, uid, [('code', '=', 'prestashop')], context=context)[0]
            referential_ids = self.pool.get('external.referential').search(cr, uid, [('type_id', '=', prestashop_type_id)], context=context)
            vals['external_referential_ids'] = [(6, 0, referential_ids)]
        return super(product_attribute, self).create(cr, uid, vals, context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
