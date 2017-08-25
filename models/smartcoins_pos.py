# -*- coding: utf-8 -*-

from openerp import models, fields, api

from assets_fetch import getExchangeRate
import requests, json
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class smartcoins_pos(models.Model):
    _name = 'smartcoins_pos.smartcoins_pos'

    name = fields.Char()
    wifkey = fields.Char()
    user_account_id = fields.Char()
    smartcoins_id = fields.Many2one(
        'smartcoins_pos.smartcoins', string="SmartCoins",delegate=True)
    user_assets_id = fields.Many2one(
        'smartcoins_pos.user_assets', string="UserIssuedAssets")
    block_trade_coin_ids = fields.Many2many(
        'smartcoins_pos.bt_smartcoins', 'bt_id', string="BlockTradeSmartCoins")
    popup_shown = fields.Boolean(default=False)
    num_of_loyalty_rps = fields.Integer()
    eq_amount_loyalty_rps = fields.Float()
    @api.model
    def get_selected_data(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            selected_data = {'name':rec[0]['name']}
            rec_selected_smartcoin = self.env['smartcoins_pos.smartcoins'].search_read([("id","=",rec[0]['smartcoins_id'][0])])
            selected_data['smartcoins'] = rec_selected_smartcoin[0]
            return selected_data
        return ""
    
    @api.model
    def get_selected_uia_data(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec and rec[0]['user_assets_id']:
            selected_data = {}
            rec_selected_smartcoin = self.env['smartcoins_pos.user_assets'].search_read([("id","=",rec[0]['user_assets_id'][0])])
            selected_data['uia'] = rec_selected_smartcoin[0]
            return selected_data
        return ""
    
    
    @api.model
    def get_selected_bt_coins(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            selected_data = {'name':rec[0]['name']}
            rec_selected_smartcoin = self.env['smartcoins_pos.bt_smartcoins'].search_read([("id","in",rec[0]['block_trade_coin_ids'])], order="name")
            selected_data['smartcoins'] = rec_selected_smartcoin
            return selected_data
        return ""
    
    @api.model
    def get_selected_bt_data(self, id, billing_amount):
        settings_rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if settings_rec:
#           selected smartcoin
            rec_selected_smartcoin = self.env['smartcoins_pos.smartcoins'].search_read([("id","=",settings_rec[0]['smartcoins_id'][0])])
            selected_smcoin_symbol = "bit" + rec_selected_smartcoin[0]["name"].lower()
            selected_smcoin_asset_id = rec_selected_smartcoin[0]["asset_id"]
            rec_bt_coin = self.env['smartcoins_pos.bt_smartcoins'].search_read([("id","=",id)])
            selected_bt_coin_type = rec_bt_coin[0]["coin_type"]
            selected_data = {}
            if checkIfTradingPairExist(selected_bt_coin_type, selected_smcoin_symbol):
                selected_data['trading_pairs'] = {'input_coin_type' : selected_bt_coin_type, 'output_coin_type' : selected_smcoin_symbol}
                estimated_amount = estimateInputAmount(billing_amount, selected_bt_coin_type, selected_smcoin_symbol)
                if estimated_amount != -1: 
                    selected_data['estimated_amount'] = estimated_amount['inputAmount']
                
            else:
                selected_data['trading_pairs'] = {'input_coin_type' : selected_bt_coin_type, 'output_coin_type' : 'bts'}
                ex_rate = getExchangeRate(selected_smcoin_asset_id, '1.3.0')
                converted_bill_amount = ex_rate * billing_amount
                estimated_amount = estimateInputAmount(converted_bill_amount, selected_bt_coin_type, 'bts')
                if estimated_amount != -1: 
                    selected_data['estimated_amount'] = estimated_amount['inputAmount']
            selected_data['selected_alt_coin_symbol'] = rec_bt_coin[0]["symbol"]
            selected_data['selected_alt_wallet_type'] = rec_bt_coin[0]["wallet_type"]
            return selected_data
        return ""
    
    @api.model
    def get_uia_settings(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            selected_data = {'amount': rec[0]['eq_amount_loyalty_rps'], 'r_points' : rec[0]['num_of_loyalty_rps'] }
            return selected_data
        return ""

    @api.model
    def getCurrency(self, base_asset_id, quote_asset_id):
        return getExchangeRate(base_asset_id, quote_asset_id)
    
def checkIfTradingPairExist(inputCoinType, outputCoinType):
    url = 'https://blocktrades.us/api/v2/trading-pairs/' + inputCoinType  + '/' + outputCoinType
    response = requests.get(url, verify=False)
    result = response.json()    
    if 'outputCoinType' in  result:
        return  True
    else:
        return False
        
def estimateInputAmount(outputAmount, inputCoinType, outputCoinType):
    url = 'https://blocktrades.us:443/api/v2/estimate-input-amount'
    params = {'outputAmount' : outputAmount, 'inputCoinType': inputCoinType, 'outputCoinType': outputCoinType}
    response = requests.get(url, params=params, verify=False)
    result = response.json()
    if 'outputCoinType' in  result:
        return result
    else:
        return -1