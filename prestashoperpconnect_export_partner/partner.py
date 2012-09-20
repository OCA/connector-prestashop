# -*- encoding: utf-8 -*-
##############################################################################
#
#    PrestaShopERPconnect export partner module for OpenERP
#    Copyright (C) 2012 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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


from openerp.osv.orm import Model
from openerp.osv import fields
import os, random, string


class res_partner(Model):
    _inherit = 'res.partner'

    _columns = {
        'prestashop_passwd': fields.char('PrestaShop password', size=32, help="When you export a partner to PrestaShop, this will be used as the initial password for the account."),
        }

    def generate_passwd(self, cr, uid, ids, context=None):
        if len(ids) != 1:
            raise # this should not happen

        chars = string.ascii_letters + string.digits
        random.seed = (os.urandom(1024))

        passwd = ''.join(random.choice(chars) for i in range(12))
        self.write(cr, uid, ids[0], {'prestashop_passwd': passwd}, context=context)
        return True


