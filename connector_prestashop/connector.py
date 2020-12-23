# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def get_environment(session, model_name, backend_id):
    _logger.warn("deprecated: please use PrestashopBackend.get_environment")
    backend = session.env["prestashop.backend"].browse(backend_id)
    return backend.get_environment(model_name, session=session)
