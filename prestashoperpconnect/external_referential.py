# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

from osv import osv, fields
import netsvc
from tools.translate import _
from base_external_referentials.decorator import only_for_referential
from prestapyt import PrestaShopWebServiceError, PrestaShopWebService, PrestaShopWebServiceDict
from prestashop_osv import prestashop_osv

class external_referential(prestashop_osv):
    _inherit = "external.referential"
    
    @only_for_referential('prestashop')
    def external_connection(self, cr, uid, id, DEBUG=False, context=None):
        logger = netsvc.Logger()
        if isinstance(id, list):
            id=id[0]
        referential = self.browse(cr, uid, id, context=context)
        prestashop = PrestaShopWebServiceDict('%s/api'%referential.location, referential.apipass)
        try:        
            prestashop.head('')
        except Exception, e:
            raise osv.except_osv(_("Connection Error"), _("Could not connect to server\nCheck url & password.\n %s"%e))
        return prestashop

    @only_for_referential('prestashop')
    def import_referential(self, cr, uid, ids, context=None):
        print 'I will import the referential'
        #TODO create shop (what we should do for version older than 1.5)
        return True
