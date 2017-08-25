# -*- coding: utf-8 -*-

from openerp import models, fields, api

class smartcoinsUserBalance(models.Model):
    _name = 'smartcoins_pos.user_balance'
    
    user_id = fields.Char()
    remaining_balance = fields.Float()
    
    @api.model
    def store_remaining_balance(self,user_id,balance):
        values = {"user_id":user_id,
                  "remaining_balance":balance}

        self.env['smartcoins_pos.user_balance'].create(values)
        
    @api.model
    def update_remaining_balance(self,user_id,balance):
        rec = self.env['smartcoins_pos.user_balance'].search([("user_id","=",user_id)])
        values = {"user_id":user_id,
                  "remaining_balance":balance}

        rec.write(values)

