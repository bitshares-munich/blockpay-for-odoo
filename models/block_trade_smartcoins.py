# -*- coding: utf-8 -*-

from openerp import models, fields, api
import requests, json
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class blocktradesmartcoins(models.Model):
    _name = 'smartcoins_pos.bt_smartcoins'
    _rec_name = 'name'

    name = fields.Char()
    coin_type = fields.Char()
    symbol = fields.Char()
    coin_selected = fields.Boolean(string='')
    deposit_adress = fields.Char()
    wallet_type = fields.Char()
    transaction_fee = fields.Float() 
    precision = fields.Float()
    backing_coin_type = fields.Char()
            
    def init(self,cr):
        self.pool.get('smartcoins_pos.assets_fetch').fetch_block_trade_coins(cr)
        pass
    
    def on_change_deposit_address(self,cr,user,ids,coin_selected,
                                  deposit_adress, wallet_type, context=None):
        res = {
            'value': {
            #This sets the total price on the field standard_price.
                    'coin_selected': False,
                    'deposit_adress' : ''
              }
        }
        if deposit_adress != "":
            url = 'https://blocktrades.us/api/v2/wallets/' + wallet_type  + '/address-validator'
            params = {'address' : deposit_adress}
            response = requests.get(url, params=params, verify=False)
            result = response.json()
            res['value']['coin_selected'] = True 
            if res['value']['coin_selected']:
                res['value']['deposit_adress'] = deposit_adress
            else:
                res['value']['deposit_adress'] = ''

        return res