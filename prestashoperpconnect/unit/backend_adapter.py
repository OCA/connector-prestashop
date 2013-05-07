# -*- coding: utf-8 -*-
##############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright 2013 Camptocamp SA
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    @author: Guewen Baconnier
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
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

import logging
from prestapyt import PrestaShopWebServiceDict
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from ..backend import prestashop

_logger = logging.getLogger(__name__)


class PrestaShopWebServiceImage(PrestaShopWebServiceDict):

    def get_image(self, resource, resource_id=None, image_id=None,
                  options=None):
        full_url = self._api_url + 'images/' + resource
        if resource_id is not None:
            full_url += "/%s" % (resource_id,)
            if image_id is not None:
                full_url += "/%s" % (image_id)
        if options is not None:
            self._validate_query_options(options)
            full_url += "?%s" % (self._options_to_querystring(options),)
        response = self._execute(full_url, 'GET')
        return {
            'type': response.headers['content-type'],
            'content': response.content,
            'id_' + resource[:-1]: resource_id,
            'id_image': image_id
        }


class PrestaShopLocation(object):

    def __init__(self, location, password):
        self.location = location
        self.password = password
        self.api_url = '%s/api' % location


class PrestaShopCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for PrestaShop """

    def __init__(self, environment):
        """

        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.Environment`
        """
        super(PrestaShopCRUDAdapter, self).__init__(environment)
        self.prestashop = PrestaShopLocation(
            self.backend_record.location,
            self.backend_record.password
        )

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError


class GenericAdapter(PrestaShopCRUDAdapter):

    _model_name = None
    _prestashop_model = None

    def connect(self):
        return PrestaShopWebServiceDict(self.prestashop.api_url,
                                       self.prestashop.password)

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        api = self.connect()
        return api.search(self._prestashop_model, filters)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        #TODO rename attributes in something better
        api = self.connect()
        res = api.get(self._prestashop_model, id, options=attributes)
        first_key = res.keys()[0]
        return res[first_key]

    def create(self, datas):
        """ Create a record on the external system """
        api = self.connect()
        res = api.add(self._prestashop_model, datas)

    #def write(self, id, data):
    #    """ Update records on the external system """
    #    api = self.connect()
    #    res = api.get(self._prestashop_model, id, options=attributes)
    #    first_key = res.keys()[0]
    #    return res[first_key]
    #    return self._call('%s.update' % self._magento_model,
    #                      [int(id), data])

    #def delete(self, id):
    #    """ Delete a record on the external system """


@prestashop
class ShopGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.shop.group'
    _prestashop_model = 'shop_groups'


@prestashop
class ShopAdapter(GenericAdapter):
    _model_name = 'prestashop.shop'
    _prestashop_model = 'shops'


@prestashop
class ResLangAdapter(GenericAdapter):
    _model_name = 'prestashop.res.lang'
    _prestashop_model = 'languages'


@prestashop
class ResCountryAdapter(GenericAdapter):
    _model_name = 'prestashop.res.country'
    _prestashop_model = 'countries'


@prestashop
class ResCurrencyAdapter(GenericAdapter):
    _model_name = 'prestashop.res.currency'
    _prestashop_model = 'currencies'


@prestashop
class AccountTaxAdapter(GenericAdapter):
    _model_name = 'prestashop.account.tax'
    _prestashop_model = 'taxes'


@prestashop
class PartnerCategoryAdapter(GenericAdapter):
    _model_name = 'prestashop.res.partner.category'
    _prestashop_model = 'groups'


@prestashop
class PartnerAdapter(GenericAdapter):
    _model_name = 'prestashop.res.partner'
    _prestashop_model = 'customers'


@prestashop
class PartnerAddressAdapter(GenericAdapter):
    _model_name = 'prestashop.address'
    _prestashop_model = 'addresses'


@prestashop
class ProductCategoryAdapter(GenericAdapter):
    _model_name = 'prestashop.product.category'
    _prestashop_model = 'categories'


@prestashop
class ProductAdapter(GenericAdapter):
    _model_name = 'prestashop.product.product'
    _prestashop_model = 'products'


@prestashop
class ProductImageAdapter(PrestaShopCRUDAdapter):
    _model_name = 'prestashop.product.image'
    _prestashop_image_model = 'products'

    def read(self, product_id, image_id, options=None):
        api = PrestaShopWebServiceImage(self.prestashop.api_url,
                                        self.prestashop.password)
        return api.get_image(
            self._prestashop_image_model,
            product_id,
            image_id,
            options=options
        )


@prestashop
class TaxGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.account.tax.group'
    _prestashop_model = 'tax_rule_groups'
