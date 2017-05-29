# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.connector.exception import RetryableJobError


class OrderImportRuleRetry(RetryableJobError):
    """ The sale order import will be retried later. """
