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

#import logging
#_logger = logging.getLogger(__name__)

def luhn_check(number):
    # https://sv.wikipedia.org/wiki/Luhn-algoritmen
    
    # Reverse number and remove '-' character.
    digits = [int(x) for x in number[::-1].replace('-', '')]
    
    # Sum every other digit starting with the first.
    odd_digitsum = sum(x for x in digits[::2])
    
    # Multiply every other digit starting with the second.
    even_digits = map(lambda x: x*2, digits[1::2])
    
    # Split and sum each individual digit.
    even_digitsum = sum(int(x) for x in ''.join(map(str, even_digits)))

    return (odd_digitsum + even_digitsum) % 10 == 0

def bg_validator(acc_number):
    # 7-8 digits: (X)XXX-XXXX
    if acc_number.replace('-', '', 1).isdigit():
        if 7 < len(acc_number) < 10:
            if acc_number[-5] == '-':
                if luhn_check(acc_number):
                    return True
    return False

def pg_validator(acc_number):
    # 2-8 digits: (XXXXXX)X-X
    if acc_number.replace('-', '', 1).isdigit():
        if 2 < len(acc_number) < 10:
            if acc_number[-2] == '-':
                if luhn_check(acc_number):
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

