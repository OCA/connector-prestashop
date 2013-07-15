# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_customize_example for OpenERP 
#   Copyright (C) 2013 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


import openerp.addons.connector.backend as backend
import openerp.addons.prestashoperpconnect.backend as prestashop_backend

prestashop_myversion = backend.Backend(parent=prestashop_backend.prestashop1500,
                                    version='1.5-myversion')
