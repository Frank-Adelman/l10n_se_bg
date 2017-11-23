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
 'summary': 'Electronic payment file for Swedish Bankgirot Leverantörsbetalningar',
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
  * This module depends on the OCA module: 'account_payment_order'.

Installation
~~~~~~~~~~~~
  * This module creates two new bank types: 'Bankgiro' and 'Plusgiro'.
  * It also creates a new payment method: 'Bankgirot Leverantörsbetalningar'

Configuration
~~~~~~~~~~~~~
  * Create a payment mode and select '[bg_link] Bankgirot Leverantörsbetalningar' as payment method, and set your company's Bankgiro account in: Invoicing > Configuration > Management > Payment Modes
  * Make sure 'Group Transactions in Payment Orders' is not checked in your payment mode.
  * Create Bankgiro or Plusgiro accounts for your suppliers.
  
Usage
~~~~~
  * When registering new invoices to later be included in a payment file, select your newly created payment mode.
  * Create a payment order from: Invoicing > Payments > Payment Orders
  * For 'Payment Mode' select your newly created payment mode then populate the payment order with the 'Create Payment Lines from Journal Items' button.
  * To generate the file, click 'Confirm Payments' button then 'Generate Payment File'.
  * Download the file and send it to your bank.
  * You can later create journal enries by clicking 'File Successfully Uploaded'.
""",
 'version': '0.2',
 'author': 'Frank Adelman',
 'category': 'Localization',
 'license': 'AGPL-3',
 'depends': ['base_iban', 'account', 'account_payment_order', 'document'],
 'data': ['data/account_payment_method_data.xml'],
 'auto_install': False,
 'installable': True,
 'images': []
 }
