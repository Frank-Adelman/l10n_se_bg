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

def luhn_check(number):
    # https://sv.wikipedia.org/wiki/Luhn-algoritmen
    # TO BE IMPLEMENTED!
    return

def bg_validator(acc_number):
    # 7-8 digits: (X)XXX-XXXX
    if 7 < len(acc_number) < 10:
        if acc_number[-5] == '-':
            return True
    return False

def pg_validator(acc_number):
    # 2-8 digits: (XXXXXX)X-X
    if 2 < len(acc_number) < 10:
        if acc_number[-2] == '-':
            return True
    return False

class ResPartnerBank(models.Model):
    
    _inherit = "res.partner.bank"

    @api.one
    @api.depends('acc_number')
    def _compute_acc_type(self):
        # At first acc_number is false, let parent method handle that.
        if not self.acc_number:
            super(ResPartnerBank, self)._compute_acc_type()
        elif bg_validator(self.acc_number):
            self.acc_type = 'bg'
        elif pg_validator(self.acc_number):
            self.acc_type = 'pg'
        else:
            super(ResPartnerBank, self)._compute_acc_type()

