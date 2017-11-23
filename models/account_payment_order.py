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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.exceptions import UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

#import logging
#_logger = logging.getLogger(__name__)

class AccountPaymentOrder(models.Model):
    
    _inherit = 'account.payment.order'
    
    @api.multi
    def generate_payment_file(self):
        """Start generating the Bankgiro payment file."""
        self.ensure_one()
        
        if self.payment_method_id.code != 'bg_link':
            return super(AccountPaymentOrder, self).generate_payment_file()
        
        self._file_content = ""
        
        self._create_opening_post()
        self._create_payment_lines()
        self._create_closing_post()

        # Encode file content.
        self._file_content = self._file_content.encode('latin1')
        file_name = 'BG%s.txt' % time.strftime(DEFAULT_SERVER_DATETIME_FORMAT, time.gmtime())
        file_name = file_name.replace(' ', '_')

        #_logger.error("DEBUG OUTPUT:\n%s", self._file_content)
        
        return (self._file_content, file_name)
    
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
        
        for line in self.bank_line_ids:
            bank_line = []
            
            bank_line.append(self._payment_type(line))
            bank_line.append(self._partner_bank(line).rjust(10, '0'))
            bank_line.append(self._payment_ref(line).ljust(25, ' '))
            bank_line.append(self._payment_amount(line).rjust(12, '0'))
            bank_line.append(self._payment_date(line))
            bank_line.append(" " * 5)
            bank_line.append(self._internal_ref(line) + "\r\n")
            
            payment_lines.append(bank_line)

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
        # Does the company have a bank account configured?
        bank = self.company_partner_bank_id or ''
        if not bank:
            raise Warning(_('No bank account set in payment mode.'))
        
        # Bank account must be of type bg.
        if not bank.acc_type == 'bg':
            raise Warning(_('Company bank account is not of type Bankgiro but: "%s".')
                          % bank.acc_type
                          )
        
        # Get company BG-number in condensed form.
        company_bg = bank.acc_number or ''
        company_bg = company_bg.replace('-', '') or ''

        return company_bg
    
    def _payment_type(self, payment_line):
        bank_type = payment_line.partner_bank_id.acc_type
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
        partner_acc = payment_line.partner_bank_id.acc_number or ''
        partner_acc = partner_acc.replace('-', '') or ''
        
        # Is account number left blank?
        if not partner_acc:
            raise Warning(_('No account number set for partner: %s.')
                          % payment_line.partner_id.name
                         )
        
        return partner_acc

    def _payment_ref(self, payment_line):
        # Set payment reference, and only return the last 25 characters.
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
        if not payment_line.currency_id.name == 'SEK':
            raise Warning(_('Can only make payments in SEK, payment to "%s" is in: %s')
                          % (payment_line.partner_id.name, payment_line.currency_id.name)
                         )
        
        return amount

    def _payment_date(self, payment_line):
        if payment_line.date:
            payment_date = fields.Date.from_string(payment_line.date)
        else:
            payment_date = datetime.now().today()

        return payment_date.strftime("%y%m%d")

    def _internal_ref(self, payment_line):
        # Invoice journal number. Could be multiple if 'Group Transactions in Payment Orders' is checked.
        ref = ''
        for id in payment_line.payment_line_ids:
            ref += id.move_line_id.move_id.name or ''
        return ref[-20:]
    
    def _payment_lines_count(self):
        return str(len(self.bank_line_ids))
    
    def _total_amount(self):
        amount = sum(line.amount_currency for line in self.bank_line_ids)
        
        # Always use 2 decimal places.
        amount = '{0:.2f}'.format(amount)
        
        # Remove decimal and '-' sign for payment ammount.
        return amount.replace('.', '').replace(',', '').replace('-', '')

    def _total_amount_negative(self):
        amount = sum(line.amount_currency for line in self.bank_line_ids)
        
        # Add trailing '-' if total amount is negative.
        if amount < 0:
            return "-"
        else:
            return ""

    # Overriding parent method to be able to process credit invoices!
    @api.multi
    def draft2open(self):
        """
        Called when you click on the 'Confirm' button
        Set the 'date' on payment line depending on the 'date_prefered'
        setting of the payment.order
        Re-generate the bank payment lines
        """
        bplo = self.env['bank.payment.line']
        today = fields.Date.context_today(self)
        for order in self:
            if not order.journal_id:
                raise UserError(_(
                                  'Missing Bank Journal on payment order %s.') % order.name)
            if not order.payment_line_ids:
                raise UserError(_(
                                  'There are no transactions on payment order %s.')
                                % order.name)
            # Delete existing bank payment lines
            order.bank_line_ids.unlink()
            # Create the bank payment lines from the payment lines
            group_paylines = {}  # key = hashcode
            for payline in order.payment_line_ids:
                payline.draft2open_payment_line_check()
                # Compute requested payment date
                if order.date_prefered == 'due':
                    requested_date = payline.ml_maturity_date or today
                elif order.date_prefered == 'fixed':
                    requested_date = order.date_scheduled or today
                else:
                    requested_date = today
                # No payment date in the past
                if requested_date < today:
                    requested_date = today
                # inbound: check option no_debit_before_maturity
                if (
                    order.payment_type == 'inbound' and
                    order.payment_mode_id.no_debit_before_maturity and
                    payline.ml_maturity_date and
                    requested_date < payline.ml_maturity_date):
                    raise UserError(_(
                        "The payment mode '%s' has the option "
                        "'Disallow Debit Before Maturity Date'. The "
                        "payment line %s has a maturity date %s "
                        "which is after the computed payment date %s.") % (
                            order.payment_mode_id.name,
                            payline.name,
                            payline.ml_maturity_date,
                            requested_date))
                # Write requested_date on 'date' field of payment line
                payline.date = requested_date
                # Group options
                if order.payment_mode_id.group_lines:
                    hashcode = payline.payment_line_hashcode()
                else:
                    # Use line ID as hascode, which actually means no grouping
                    hashcode = payline.id
                if hashcode in group_paylines:
                    group_paylines[hashcode]['paylines'] += payline
                    group_paylines[hashcode]['total'] +=\
                        payline.amount_currency
                else:
                    group_paylines[hashcode] = {
                        'paylines': payline,
                        'total': payline.amount_currency,
                    }
            # Create bank payment lines
            for paydict in group_paylines.values():
                # EDITED: Only do this check for non 'bg_link' type payments.
                if self.payment_method_id.code != 'bg_link':
                    # Block if a bank payment line is <= 0
                    if paydict['total'] <= 0:
                        raise UserError(_(
                            "The amount for Partner '%s' is negative "
                            "or null (%.2f) !")
                            % (paydict['paylines'][0].partner_id.name,
                                paydict['total']))
                # END EDIT
                vals = self._prepare_bank_payment_line(paydict['paylines'])
                bplo.create(vals)
        self.write({'state': 'open'})
        return True

    # Overriding parent method to be able to process credit invoices!
    @api.multi
    def _prepare_move_line_offsetting_account(
            self, amount_company_currency, amount_payment_currency, bank_lines):
        
        vals = super(AccountPaymentOrder, self)._prepare_move_line_offsetting_account(amount_company_currency,
                                                                                      amount_payment_currency,
                                                                                      bank_lines)

        if self.payment_type == 'outbound' and amount_company_currency < 0:
            vals['credit'] = 0.0
            vals['debit'] = abs(amount_company_currency)

        return vals

    # Overriding parent method to be able to process credit invoices!
    @api.multi
    def _prepare_move_line_partner_account(self, bank_line):
        vals = super(AccountPaymentOrder, self)._prepare_move_line_partner_account(bank_line)

        if self.payment_type == 'outbound' and bank_line.amount_company_currency < 0:
            vals['credit'] = abs(bank_line.amount_company_currency)
            vals['debit'] = 0.0

        return vals
