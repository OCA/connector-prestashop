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


class PrestaShopLocation(object):

    def __init__(self, location, password):
        self.location = location
        self.password = password
        self.api_url = '%s/api'%location


class PrestaShopCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for PrestaShop """

    def __init__(self, environment):
        """

        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.Environment`
        """
        super(PrestaShopCRUDAdapter, self).__init__(environment)
        self.prestashop = PrestaShopLocation(self.backend_record.location,
                                       self.backend_record.password)

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

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        api = PrestaShopWebServiceDict(self.prestashop.api_url,
                self.prestashop.password)
        return api.search(self._prestashop_model, filters)
        return []

    def read(self, id, attributes=None): 
        """ Returns the information of a record

        :rtype: dict
        """
        #TODO rename attributes in something better
        api = PrestaShopWebServiceDict(self.prestashop.api_url,
                self.prestashop.password)
        res = api.get(self._prestashop_model, id, options=attributes)
        first_key = res.keys()[0]
        return res[first_key]
        return {}

    def create(self, data):
        """ Create a record on the external system """
#        with magentolib.API(self.magento.location,
#                            self.magento.username,
#                            self.magento.password) as api:
#            _logger.debug("api.call(%s.create', [%s])", self._magento_model, data)
#            return api.call('%s.create' % self._magento_model, [data])

    def write(self, id, data):
        """ Update records on the external system """
#        with magentolib.API(self.magento.location,
#                            self.magento.username,
#                            self.magento.password) as api:
#            _logger.debug("api.call(%s.update', [%s, %s])",
#                    self._magento_model, id, data)
#            return api.call('%s.update' % self._magento_model, [id, data])

    def delete(self, id):
        """ Delete a record on the external system """
#        with magentolib.API(self.magento.location,
#                            self.magento.username,
#                            self.magento.password) as api:
#            _logger.debug("api.call(%s.delete', [%s])",
#                    self._magento_model, id)
#            return api.call('%s.delete' % self._magento_model, [id])


@prestashop
class ShopGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.shop.group'
    _prestashop_model = 'shop_groups'

@prestashop
class ShopAdapter(GenericAdapter):
    _model_name = 'prestashop.shop'
    _prestashop_model = 'shops'

@prestashop
class CurrencyAdapter(GenericAdapter):
    _model_name = 'res.currency'
    _prestashop_model = 'currencies'

@prestashop
class CountryAdapter(GenericAdapter):
    _model_name = 'res.country'
    _prestashop_model = 'countries'

@prestashop
class LangAdapter(GenericAdapter):
    _model_name = 'res.lang'
    _prestashop_model = 'languages'

#@prestashop
#class PartnerAdapter(GenericAdapter):
#    _model_name = 'prestashop.res.partner'
#    _prestashop_model = 'customers'

