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

{'name': 'Sweden - Bankgiro Payment File',
 'summary': 'Electronic payment file for Swedish Bankgiro Leverantörsbetalningar',
 'description': """
Generate payment files to the Swedish Bankgiro.
-----------------------------------------------

Supported Features
~~~~~~~~~~~~~~~~~~
  * Debit invoice payment to Bankgiro account.
  * Credit invoice decuction to Bankgiro account. (Credit amount will stay open at the Bankgiro-central and deduct from debit amounts until fully deducted.)
  * Debit invoice payment to Plusgiro account.

Prerequisite
~~~~~~~~~~~~
  * Activate Bankgiro payment files at your bank.

Installation
~~~~~~~~~~~~
  * This module adds two new bank types: 'Bankgiro' and 'Plusgiro'.

Configuration
~~~~~~~~~~~~~
  * Setup your company's Bankgiro account in: Settings -> Companies -> Bank Accounts
  * Create a payment mode and select your Bankgiro account in: Accounting -> Configuration -> Miscellaneous -> Payment Mode
  * Create Bankgiro or Plusgiro accounts for your suppliers.
  
Usage
~~~~~
  * Create a payment order from: Accounting -> Payment -> Payment Orders
  * For 'Payment Mode' select your newly created payment mode then populate the payment order with the 'Invoices' button.
  * To generate the file, click 'Generate BG File' from the 'More' button.
  * The file can now be downloaded from the 'Attachment(s)' button.
  * Send the file to your bank.
""",
 'version': '0.1',
 'author': 'Frank Adelman',
 'category': 'Localization',
 'license': 'AGPL-3',
 'depends': ['base', 'account_payment', 'document'],
 'data': ['data/res.partner.bank.type.csv',
          'wizard/payment_order_views.xml'],
 'auto_install': False,
 'installable': True,
 'images': []
 }
