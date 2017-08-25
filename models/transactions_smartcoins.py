# -*- coding: utf-8 -*-

from openerp import models, fields, api

class smartcoinsTransactions(models.Model):
    _name = 'smartcoins_pos.smartcoins_transactions'
    _rec_name = 'order'

    order = fields.Char()
    block = fields.Char()
    transaction = fields.Text()
    
    @api.model
    def store_transactions(self,order,block,trx):
        values = {"order":order,
                  "block":block,
                  "transaction":trx}

        rec = self.env['smartcoins_pos.smartcoins_transactions'].search([("order","=",order)])
        if not rec:
            self.env['smartcoins_pos.smartcoins_transactions'].create(values)

    @api.model
    def check_order_transaction(self, order):
        print order
        rec = self.env['smartcoins_pos.smartcoins_transactions'].search_read([("order","=",order)])
        if rec:
            print rec[0]
            return rec[0]
        else: 
            return
