# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.checkpoint import checkpoint
import logging

_logger = logging.getLogger(__name__)


def add_checkpoint(session, model_name, record_id, backend_id):
    """ Add a row in the model ``connector.checkpoint`` for a record,
    meaning it has to be reviewed by a user.

    :param session: current session
    :type session: \
      :py:class:`openerp.addons.connector.session.ConnectorSession`
    :param model_name: name of the model of the record to be reviewed
    :type model_name: str
    :param record_id: ID of the record to be reviewed
    :type record_id: int
    :param backend_id: ID of the PrestaShop Backend
    :type backend_id: int
    """
    return checkpoint.add_checkpoint(session, model_name, record_id,
                                     'prestashop.backend', backend_id)


def get_environment(session, model_name, backend_id):
    _logger.warn('deprecated: please use PrestashopBackend.get_environment')
    backend = session.env['prestashop.backend'].browse(backend_id)
    return backend.get_environment(model_name, session=session)
