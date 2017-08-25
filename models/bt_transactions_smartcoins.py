# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class bt_smartcoinsTransactions(models.Model):
    _name = 'smartcoins_pos.bt_smartcoins_transactions'
    _rec_name = 'order'

    order = fields.Char()
    deposit_address = fields.Char()
    transaction_status = fields.Boolean(string='')
    
    @api.model
    def store_transactions(self, order, deposit_address, transaction_status):
        values = {"order":order,
                  "deposit_address":deposit_address,
                  "transaction_status":transaction_status}
 
        rec = self.env['smartcoins_pos.bt_smartcoins_transactions'].search([("order","=",order)])
        if not rec:
            self.env['smartcoins_pos.bt_smartcoins_transactions'].create(values)

    @api.model
    def check_order_transaction(self, order):
        print order
        rec = self.env['smartcoins_pos.bt_smartcoins_transactions'].search_read([("order","=",order)])
        if rec:
            print rec[0]
            return rec[0]
        else: 
            return
