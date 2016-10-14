# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import exceptions, _
from openerp.addons.connector.exception import NetworkRetryableError
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter

from contextlib import contextmanager
from requests.exceptions import HTTPError, RequestException, ConnectionError
import base64
import logging
_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


@contextmanager
def api_handle_errors(message=''):
    """ Handle error when calling the API

    It is meant to be used when a model does a direct
    call to a job using the API (not using job.delay()).
    Avoid to have unhandled errors raising on front of the user,
    instead, they are presented as :class:`openerp.exceptions.UserError`.
    """
    if message:
        message = message + u'\n\n'
    try:
        yield
    except NetworkRetryableError as err:
        raise exceptions.UserError(
            _(u'{}Network Error:\n\n{}').format(message, err)
        )
    except (HTTPError, RequestException, ConnectionError) as err:
        raise exceptions.UserError(
            _(u'{}API / Network Error:\n\n{}').format(message, err)
        )
    except PrestaShopWebServiceError as err:
        raise exceptions.UserError(
            _(u'{}Authentication Error:\n\n{}').format(message, err)
        )
    except PrestaShopWebServiceError as err:
        raise exceptions.UserError(
            _(u'{}Error during synchronization with '
                'PrestaShop:\n\n{}').format(message, unicode(err))
        )


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
        if response.content:
            image_content = base64.b64encode(response.content)
        else:
            image_content = ''

        return {
            'type': response.headers['content-type'],
            'content': image_content,
            'id_' + resource[:-1]: resource_id,
            'id_image': image_id
        }


class PrestaShopLocation(object):

    def __init__(self, location, webservice_key):
        self.location = location
        self.webservice_key = webservice_key
        if not location.endswith('/api'):
            location = location + '/api'
        if not location.startswith('http'):
            location = 'http://' + location
        self.api_url = location


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
        self.client = PrestaShopWebServiceDict(
            self.prestashop.api_url,
            self.prestashop.webservice_key,
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

    def head(self):
        """ HEAD """
        raise NotImplementedError


class GenericAdapter(PrestaShopCRUDAdapter):

    _model_name = None
    _prestashop_model = None

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        _logger.debug(
            'method search, model %s, filters %s',
            self._prestashop_model, unicode(filters))
        return self.client.search(self._prestashop_model, filters)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        _logger.debug(
            'method read, model %s id %s, attributes %s',
            self._prestashop_model, str(id), unicode(attributes))
        res = self.client.get(self._prestashop_model, id, options=attributes)
        first_key = res.keys()[0]
        return res[first_key]

    def create(self, attributes=None):
        """ Create a record on the external system """
        _logger.debug(
            'method create, model %s, attributes %s',
            self._prestashop_model, unicode(attributes))
        return self.client.add(self._prestashop_model, {
            self._export_node_name: attributes
        })

    def write(self, id, attributes=None):
        """ Update records on the external system """
        attributes['id'] = id
        _logger.debug(
            'method write, model %s, attributes %s',
            self._prestashop_model,
            unicode(attributes)
        )
        return self.client.edit(
            self._prestashop_model, {self._export_node_name: attributes})

    def delete(self, resource, ids):
        _logger.debug('method delete, model %s, ids %s',
                      resource, unicode(ids))
        # Delete a record(s) on the external system
        return self.client.delete(resource, ids)

    def head(self, id=None):
        """ HEAD """
        return self.client.head(self._prestashop_model, resource_id=id)
