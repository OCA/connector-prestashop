# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.checkpoint import checkpoint


def add_checkpoint(session, model_name, record_id, backend_id, message=''):
    """Add checkpoint for prestashop backend."""
    return checkpoint.add_checkpoint(session, model_name, record_id,
                                     'prestashop.backend', backend_id)


def add_checkpoint_message(session, backend_id, message=''):
    """Add checkpoint message for prestashop backend."""
    return checkpoint.add_checkpoint_message(
        session, 'prestashop.backend', backend_id, message=message)


def get_environment(session, model_name, backend_id):
    backend_record = session.env['prestashop.backend'].browse(backend_id)
    return ConnectorEnvironment(backend_record, session, model_name)
