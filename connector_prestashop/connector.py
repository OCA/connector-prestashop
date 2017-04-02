# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.connector import ConnectorEnvironment


def get_environment(session, model_name, backend_id):
    backend_record = session.env['prestashop.backend'].browse(backend_id)
    return ConnectorEnvironment(backend_record, session, model_name)
