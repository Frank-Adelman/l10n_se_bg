# -*- coding: utf-8 -*-
#############################################################################
#    Odoo module for generating a Swedish Bankgiro payment file.
#    Copyright (C) 2017 Frank Adelman <adelman.frank@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

from openerp import models, fields, api

class Type(models.Model):
    
    _inherit = "res.partner.bank.type"
    
    @api.model
    def create_bank_type(self):
        # Create new bank types 'Bankgiro' & 'Plusgiro' if they don't already exist.
        bg = self.search_count([('code', '=', 'bg')])
        pg = self.search_count([('code', '=', 'pg')])
        
        if not bg:
            self.create({
                        'id': 'bg',
                        'code': 'bg',
                        'name': 'Bankgiro'
                        })
                
        if not pg:
            self.create({
                        'id': 'pg',
                        'code': 'pg',
                        'name': 'Plusgiro'
                        })
