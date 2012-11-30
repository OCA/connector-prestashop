# -*- encoding: utf-8 -*-
##############################################################################
#
#    PrestaShopERPconnect simple bundle module for OpenERP
#    Copyright (C) 2012 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv.orm import Model
from tools.translate import _
from prestapyt import PrestaShopWebServiceError
import logging

_logger = logging.getLogger(__name__)


class sale_order_line(Model):
    _inherit = 'sale.order.line'

    def _get_so_line_details(self, cr, uid, external_session, ps_order_row_id, context=None):
        resource = super(sale_order_line, self)._get_so_line_details(cr, uid, external_session, ps_order_row_id, context=context)
        # Check that this product is mapped
        ps_product_id = resource[0]['product_id']
        if self.pool.get('product.product').get_oeid(cr, uid, ps_product_id, external_session.referential_id.id, context=context):
            return resource
        else:
            product_pack_res = external_session.connection.get('products', ps_product_id)
            if not product_pack_res['product'].get('type'):
                raise osv.except_osv(_('Error :'), _("Your PrestaShop instance doesn't have support for products packs via the webservices."))

            resource_pack = []
            if product_pack_res['product']['type'].get('value') != 'pack':
                return resource
            else:
                _logger.info('Product of type pack detected in PrestaShop order line ID %d' %ps_order_row_id)
                # Here, we generate our own "resource" based on the composition
                # of the pack
                for pack_bom_line in product_pack_res['product']['associations']['product_bundle']['product']:
                    resource_pack.append({
                        'id_order': resource[0]['id_order'],
                        'product_id': pack_bom_line['id'],
                        'reduction_percent': resource[0]['reduction_percent'],
                        'product_quantity': str(int(pack_bom_line['quantity']) * int(resource[0]['product_quantity'])),
                        'taxes': resource[0]['taxes'],
                    })
                return resource_pack
