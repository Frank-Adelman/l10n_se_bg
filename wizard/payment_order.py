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

import time
from datetime import datetime
import base64

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

#import logging
#_logger = logging.getLogger(__name__)

class BGFileGenerator(models.TransientModel):
    """Class for generating a Swedish Bankgiro payment file."""
    
    _name = "payment.order.bgfilegenerator"
    
    @api.multi
    def action_generate_file(self):
        """Start generating the Bankgiro payment file."""
        
        active_id = self._context.get('active_id', [])
        self._payment_order = self.env['payment.order'].browse(active_id)

        if not self._payment_order.line_ids:
            raise Warning(_('There are no payment lines.'))
        
        self._file_content = ""
        
        self._create_opening_post()
        self._create_payment_lines()
        self._create_closing_post()

        # Encode file content.
        self._file_content = self._file_content.encode('latin1')
        data = base64.b64encode(self._file_content)

        #_logger.error("DEBUG OUTPUT:\n%s", self._file_content)

        # Save data as attachment.
        file_name = 'BG%s.txt' % time.strftime(DEFAULT_SERVER_DATETIME_FORMAT, time.gmtime())
        dict = {
            'name': file_name.replace(' ', '_'),
            'datas': data,
            #'datas_fname': file_name,
            'res_model': 'payment.order',
            'res_id': active_id
        }
        self.env['ir.attachment'].create(dict)
    
    def _create_opening_post(self):
        """Create the opening post for the file in the format of:
            11BBBBBBBBBBYYMMDDLEVERANTÖRSBETALNINGAR
            where the leading 11 is a transaction code for opening post,
            followed by company BG-number in 10 digits prefixed by zeros,
            followed by date of file generation in format YYMMDD,
            followed by a mandatory text."""
        
        self._file_content += "11"
        self._file_content += self._company_bank().rjust(10, '0')
        self._file_content += time.strftime('%y%m%d')
        self._file_content += u"LEVERANTÖRSBETALNINGAR\r\n"
    
    def _create_payment_lines(self):
        """Create a payment line in the format of:
            14BBBBBBBBBBRRRRRRRRRRRRRRRRRRRRRRRRRAAAAAAAAAAAAYYMMDD     OOOOOOOOOOOOOOOOOOOO
            where the leading 2 digits are the transaction code (14 = Bankgiro),
            followed by the partners BG/PG-number in 10 digits prefixed by zeros,
            followed by the payment reference in 25 characters suffixed by spaces,
            followed by the payment amount in kronor and ören without any decimal,
            followed by the payment date in format YYMMDD,
            followed by 5 spaces,
            followed by an optional internal reference in max 20 characters."""
        
        payment_lines = []
        
        for pline in self._payment_order.line_ids:
            payment_line = []
            
            payment_line.append(self._payment_type(pline))
            payment_line.append(self._partner_bank(pline).rjust(10, '0'))
            payment_line.append(self._payment_ref(pline).ljust(25, ' '))
            payment_line.append(self._payment_amount(pline).rjust(12, '0'))
            payment_line.append(self._payment_date(pline))
            payment_line.append(" " * 5)
            payment_line.append(self._internal_ref(pline) + "\r\n")
            
            payment_lines.append(payment_line)

        # Sort payment lines by bank account and by payment type.
        # Credit lines should be below any debet lines for each partner.
        payment_lines.sort(key=lambda x: (x[1], x[0]))

        # Convert list to string.
        self._file_content += ''.join(str(elem) for line in payment_lines for elem in line)

    def _create_closing_post(self):
        """Create the closing post for the file in the format of:
            29BBBBBBBBBBNNNNNNNNAAAAAAAAAAAA-
            where the leading 29 is a transaction code for closing post,
            followed by company BG-number in 10 digits prefixed by zeros,
            followed by the number of payment lines in 8 digits prefixed by zeros,
            followed by the total payment amount in kronor and ören without any decimal,
            followed by '-' if the total is negative."""
        
        self._file_content += "29"
        self._file_content += self._company_bank().rjust(10, '0')
        self._file_content += self._payment_lines_count().rjust(8, '0')
        self._file_content += self._total_amount().rjust(12, '0')
        self._file_content += self._total_amount_negative()

    def _company_bank(self):
        # Have payment mode been set on payment order header?
        if not self._payment_order.mode:
            raise Warning(_('No payment mode set on payment order.'))
        
        # Does the company have a bank account configured?
        bank = self._payment_order.mode.bank_id
        if not bank:
            raise Warning(_('No bank account set in payment mode.'))
        
        # Bank account must be of type bg.
        if not bank.state == 'bg':
            raise Warning(_('Company bank account is not of type Bankgiro but: "%s".')
                          % bank.state
                          )
        
        # Get company BG-number in condensed form.
        company_bg = bank.acc_number or ''
        company_bg = company_bg.replace('-', '') or ''

        # Is account number left blank?
        if not company_bg:
            raise Warning(_('No BG-number set for the company.'))
        
        # Don't allow for too long account number.
        if len(company_bg) > 10:
             raise Warning(_('Company BG-number has too many digits: %s, '
                             'only 10 is allowed.') % len(company_bg)
                          )
        
        return company_bg
    
    def _payment_type(self, payment_line):
        bank_type = payment_line.bank_id.state
        payment_amount = payment_line.amount_currency
        
        if bank_type == 'bg' and payment_amount >= 0:
            return "14"
        elif bank_type == 'bg' and payment_amount < 0:
            return "16"
        elif bank_type == 'pg' and payment_amount > 0:
            return "54"
        elif bank_type == 'pg' and payment_amount <= 0:
            raise Warning(_('Cannot process zero or negative amounts to Plusgiro for partner: %s.')
                          % payment_line.partner_id.name
                         )
        else:
            raise Warning(_('Not a valid bank account type set for partner: %s')
                          % payment_line.partner_id.name
                         )
    
    def _partner_bank(self, payment_line):
        # Get partners account number in condensed form.
        partner_acc = payment_line.bank_id.acc_number or ''
        partner_acc = partner_acc.replace('-', '') or ''
        
        # Is account number left blank?
        if not partner_acc:
            raise Warning(_('No account number set for partner: %s.')
                          % payment_line.partner_id.name
                         )
        
        # Don't allow for too long account number.
        if len(partner_acc) > 10:
            raise Warning(_('Account number for partner "%s" has too many digits: %s, '
                            'only 10 is allowed.') % (payment_line.partner_id.name, len(partner_acc))
                         )
        
        return partner_acc

    def _payment_ref(self, payment_line):
        # Set payment reference in order of existence: 'Payment Reference', 'Supplier Invoice Number', 'Voucher Number'
        # Only return that last 25 characters.
        return payment_line.communication[-25:]

    def _payment_amount(self, payment_line):
        # Always use 2 decimal places.
        amount = '{0:.2f}'.format(payment_line.amount_currency)
        # Remove decimal and '-' sign for payment amount.
        amount = amount.replace('.', '').replace(',', '').replace('-', '')
        
        # Don't allow for amount to be too big.
        if len(amount) > 12:
            raise Warning(_('Payment amount to "%s" is too big.')
                          % payment_line.partner_id.name
                         )
        
        # Check for payment in SEK.
        if not payment_line.currency.name == 'SEK':
            raise Warning(_('Can only make payments in SEK, payment to "%s" is in: %s')
                          % (payment_line.partner_id.name, payment_line.currency.name)
                         )
        
        return amount

    def _payment_date(self, payment_line):
        # Get payment date from payment order header if any.
        if payment_line.order_id.date_scheduled:
            payment_date = fields.Date.from_string(payment_line.order_id.date_scheduled)
        # Get payment date from payment order line field: Payment Date.
        elif payment_line.date:
            payment_date = fields.Date.from_string(payment_line.date)
        # If no dates set, use todays date.
        else:
            payment_date = datetime.now().today()

        return payment_date.strftime("%y%m%d")

    def _internal_ref(self, payment_line):
        # Invoice journal number.
        return payment_line.move_line_id.invoice.number or ''

    def _payment_lines_count(self):
        return str(len(self._payment_order.line_ids))
    
    def _total_amount(self):
        amount = sum(pline.amount_currency for pline in self._payment_order.line_ids)
        
        # Always use 2 decimal places.
        amount = '{0:.2f}'.format(amount)
        
        # Remove decimal and '-' sign for payment ammount.
        return amount.replace('.', '').replace(',', '').replace('-', '')

    def _total_amount_negative(self):
        amount = sum(pline.amount_currency for pline in self._payment_order.line_ids)
        
        # Add trailing '-' if total amount is negative.
        if amount < 0:
            return "-"
        else:
            return ""
