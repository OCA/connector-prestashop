# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
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
        if response[2]:
            image_content = base64.b64encode(response[2])
        else:
            image_content = ''

        return {
            'type': response[1]['content-type'],
            'content': image_content,
            'id_' + resource[:-1]: resource_id,
            'id_image': image_id
        }


class PrestaShopLocation(object):

    def __init__(self, location, webservice_key):
        self.location = location
        self.webservice_key = webservice_key
        self.api_url = '%s/api' % location


class PrestaShopCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for PrestaShop """

    def __init__(self, environment):
        """

        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(PrestaShopCRUDAdapter, self).__init__(environment)
        self.prestashop = PrestaShopLocation(
            self.backend_record.location.encode(),
            self.backend_record.webservice_key
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
                                        self.prestashop.webservice_key)

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        _logger.info(
            'method search, model %s, filters %s',
            self._prestashop_model, unicode(filters))
        api = self.connect()
        return api.search(self._prestashop_model, filters)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        _logger.info(
            'method read, model %s id %s, attributes %s',
            self._prestashop_model, str(id), unicode(attributes))
        # TODO rename attributes in something better
        api = self.connect()
        res = api.get(self._prestashop_model, id, options=attributes)
        first_key = res.keys()[0]
        return res[first_key]

    def create(self, attributes=None):
        """ Create a record on the external system """
        _logger.info(
            'method create, model %s, attributes %s',
            self._prestashop_model, unicode(attributes))
        api = self.connect()
        return api.add(self._prestashop_model, {
            self._export_node_name: attributes
        })

    def write(self, id, attributes=None):
        """ Update records on the external system """
        api = self.connect()
        attributes['id'] = id
        _logger.info(
            'method write, model %s, attributes %s',
            self._prestashop_model,
            unicode(attributes)
        )
        return api.edit(
            self._prestashop_model, id, {self._export_node_name: attributes})

    def delete(self, resource, ids):
        _logger.info('method delete, model %s, ids %s', resource, unicode(ids))
        api = self.connect()
        # Delete a record(s) on the external system
        return api.delete(resource, ids)


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
class ProductImageAdapter(PrestaShopCRUDAdapter):
    _model_name = 'prestashop.product.image'
    _prestashop_image_model = 'products'
    _prestashop_model = '/images/products'
    _export_node_name = '/images/products'

    def read(self, product_tmpl_id, image_id, options=None):
        api = PrestaShopWebServiceImage(self.prestashop.api_url,
                                        self.prestashop.webservice_key)
        return api.get_image(
            self._prestashop_image_model,
            product_tmpl_id,
            image_id,
            options=options
        )

    def create(self, attributes=None):
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        template_binder = self.binder_for('prestashop.product.template')
        template = template_binder.to_backend(
            attributes['id_product'], wrap=True)
        url = '{}/{}'.format(self._prestashop_model, template)
        return api.add(url, files=[(
            'image',
            attributes['filename'].encode('utf-8'),
            base64.b64decode(attributes['content'])
        )])

    def write(self, id, attributes=None):
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        template_binder = self.binder_for('prestashop.product.template')
        template = template_binder.to_backend(
            attributes['id_product'], wrap=True)
        url = '{}/{}'.format(self._prestashop_model, template)
        url_del = '{}/{}/{}/{}'.format(
            api._api_url, self._prestashop_model, template, id)
        try:
            api._execute(url_del, 'DELETE')
        except:
            pass
        return api.add(url, files=[(
            'image',
            attributes['filename'].encode('utf-8'),
            base64.b64decode(attributes['content'])
        )])

    def delete(self, resource, id):
        """ Delete a record on the external system """
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        return api.delete(resource, resource_ids=id)


@prestashop
class SupplierImageAdapter(PrestaShopCRUDAdapter):
    _model_name = 'prestashop.supplier.image'
    _prestashop_image_model = 'suppliers'

    def read(self, supplier_id, options=None):
        api = PrestaShopWebServiceImage(self.prestashop.api_url,
                                        self.prestashop.webservice_key)
        res = api.get_image(
            self._prestashop_image_model,
            supplier_id,
            options=options
        )
        return res['content']


@prestashop
class TaxGroupAdapter(GenericAdapter):
    _model_name = 'prestashop.account.tax.group'
    _prestashop_model = 'tax_rule_groups'


@prestashop
class OrderPaymentAdapter(GenericAdapter):
    _model_name = '__not_exist_prestashop.payment'
    _prestashop_model = 'order_payments'


@prestashop
class OrderDiscountAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.line.discount'
    _prestashop_model = 'order_discounts'


@prestashop
class SupplierAdapter(GenericAdapter):
    _model_name = 'prestashop.supplier'
    _prestashop_model = 'suppliers'


@prestashop
class SupplierInfoAdapter(GenericAdapter):
    _model_name = 'prestashop.product.supplierinfo'
    _prestashop_model = 'product_suppliers'


@prestashop
class MailMessageAdapter(GenericAdapter):
    _model_name = 'prestashop.mail.message'
    _prestashop_model = 'messages'


@prestashop
class PricelistAdapter(GenericAdapter):
    _model_name = 'prestashop.groups.pricelist'
    _prestashop_model = 'groups'
