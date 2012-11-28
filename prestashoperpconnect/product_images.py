# -*- encoding: utf-8 -*-
###############################################################################
#
#   Prestashoperpconnect for OpenERP
#   Copyright (C) 2012 Akretion (http://www.akretion.com/)
#   Authors :
#           Alexis de Lattre <alexis.delattre@akretion.com>
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
from tools.translate import _
from prestapyt import PrestaShopWebServiceError
import logging

_logger = logging.getLogger(__name__)

class product_images(osv.osv):
    _inherit = "product.images"


    def call_prestashop_method(self, cr, uid, external_session, resource_id, resource, method, mapping=None, mapping_id=None, context=None):
        """How this function works if very particular :
        with the PrestaShop webservice, I can't edit an existing image
        (if you have the proof that it is possible with PS 1.5, please contact
        me by email : alexis.delattre@akretion.com)
        So, if an image is changed in OpenERP, I have to delete the old image
        in PrestaShop and create a new one. So, if method=='edit', then
        the image is deleted via external_session.connection.delete(), then
        the mapping is deleted, and then we do an 'add' """

        # TODO : there is an important pb currently :
        # if the code fails somewhere in this function, the
        # data may become incoherent between Openerp images, PrestaShop images
        # and the content of ir_model_data
        # To help on this, we could do a "cr.commit()" between the deletion
        # of the image and its re-creation, but, according to Seb, il would break
        # the reporting system of the connector
        res = None

        img_filename = resource['image'].get('image_filename')
        if not img_filename:
            raise osv.except_osv(_('Error'), _("Missing filename on image ID %d" % resource_id))

        _logger.info("Start call_prestashop_method for product.images with method '%s' for resource_id '%d'" % (method, resource_id))
        if method == 'edit':
            ps_method = mapping[mapping_id]['external_update_method'] or method
            # Delete image if it already exists in PS
            # If can't search directly in /api/images/products/ID, because I get
            # a 500 error if the product has no image
            # So i have to search first on /apt/images/products/
            ps_product_with_image_ids = external_session.connection.search(mapping[mapping_id]['external_resource_name'])
            if resource['image'].get('product_id') in ps_product_with_image_ids:
                ps_product_image_ids = external_session.connection.search(mapping[mapping_id]['external_resource_name'] + '/' + str(resource['image'].get('product_id')))
                if ps_product_image_ids and resource['image'].get('id') in ps_product_image_ids:
                    _logger.info("Deleting image PS ID %d for product PS ID %d" % (resource['image'].get('id'), resource['image'].get('product_id')))
                    external_session.connection.delete(mapping[mapping_id]['external_resource_name'] + '/' + str(resource['image'].get('product_id')), resource['image'].get('id'))
                    model_data_obj = self.pool.get('ir.model.data')
                    model_data_id_to_delete = model_data_obj.search(cr, uid, [
                        ('name', '=', self.prefixed_id(resource['image'].get('id'))),
                        ('model', '=', self._name),
                        ('referential_id', '=', external_session.referential_id.id)
                        ], context=context)
                    if len(model_data_id_to_delete) != 1:
                        raise
                    else:
                        _logger.info('Deleting ir_model_data corresponding to image PS ID %d' % resource['image'].get('id'))
                        model_data_obj.unlink(cr, uid, model_data_id_to_delete, context=context)

        _logger.info('Pushing product image %s from OE to PrestaShop product ID %d' % (img_filename, resource['image'].get('product_id')))

        try:
            res = getattr(external_session.connection, mapping[mapping_id]['external_create_method'] or 'add')(mapping[mapping_id]['external_resource_name'] + '/' + str(resource['image'].get('product_id')), resource['image'].get('image_binary'), img_filename=img_filename)
            print "product_image add res=", res
            if method == 'edit':
                # I recreate the mapping
                self.create_external_id_vals(cr, uid, resource_id, res, external_session.referential_id.id, context=context)
        except PrestaShopWebServiceError, e:
            _logger.warning("PrestaShop webservice answered an error. HTTP error code: %s, PrestaShop error code: %s, PrestaShop error message: %s" % (e.error_code, e.ps_error_code, e.ps_error_msg))
            raise osv.except_osv(_('PrestaShop Webservice Error:'), e.ps_error_msg)
        return res

