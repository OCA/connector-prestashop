# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector_prestashop.unit.mapper import PartnerImportMapper
from .backend import prestashop_myversion


class PrestashopResPartner(models.Model):
    _inherit = 'prestashop.res.partner'

    prestashop_created_date = fields.Datetime(
        string='PrestaShop create date',
        readonly=True
    )


@prestashop_myversion
class MyPartnerImportMapper(PartnerImportMapper):
    _model_name = 'prestashop.res.partner'

    direct = (
        PartnerImportMapper.direct + [('prestashop_created_date', 'date_add')])

    @mapping
    def name(self, record):
        res = super(MyPartnerImportMapper, self).name(record)
        res['name'] = "Il est pit ton nom : %s" % res['name']
        return res
