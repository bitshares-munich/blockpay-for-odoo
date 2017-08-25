# -*- coding: utf-8 -*-

from openerp import models, fields, api
import requests, json
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class smartcoins_pos_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'smartcoins_pos.config.settings'

    default_name = fields.Char(default=lambda self: self._get_name(), required=True)
    default_wifkey = fields.Char(default=lambda self: self._get_wifkey(), required=True, string="WifKey")
    default_smartcoins_id = fields.Many2one('smartcoins_pos.smartcoins', string="Smartcoins",default=lambda self: self._get_smartcoins_id())
    default_user_assets_id = fields.Many2one('smartcoins_pos.user_assets', string='Customer Loyalty “Rewards Card”',default=lambda self: self._get_user_assets_id())
    is_valid = fields.Boolean(store=False, default=False)
    default_block_trade_coins = fields.Many2many('smartcoins_pos.bt_smartcoins', string='Altcoins', default=lambda self: self._get_bt_smartcoins_ids())
    default_popup_shown = fields.Boolean(default=lambda self: self._get_popup_shown())
    selected_block_trade_coins = fields.Many2many('smartcoins_pos.bt_smartcoins', string='Altcoins', default=lambda self: self._get_bt_smartcoins_ids())
    loyalty_rps = fields.Integer(default=lambda self: self._get_loyalty_rps(), string="Reward Points")
    loyalty_rps_equivalent = fields.Float(default=lambda self: self._get_loyalty_rps_equivalent(), string="Equivalent Amount")
    loyalty_pts_label = fields.Char(string="")
       
    @api.onchange('default_name')
    def _onchange_name(self):
        account_name = self.default_name
        if account_name and len(account_name) >= 3:        
            url = 'https://bitshares.openledger.info/ws/'
            data = {"id":2,"method":"get_account_by_name","params":[account_name]}
            headers = {'content-type': 'application/json'}
             
            response = requests.post(url, data=json.dumps(data), headers=headers)
            json_data = json.loads(response.text)
            if json_data['result'] is None:
                self.is_valid = False
                return {
                    'warning': {'title': "Warning", 'message': "Invalid Account Name"},
                }
            else:
                self.is_valid = True

    @api.one
    def set_smartcoins_pos_values(self):
        block_trade_coins_ids_list = [btcoin.id for btcoin in self.selected_block_trade_coins if btcoin.coin_selected]    
        url = 'https://bitshares.openledger.info/ws/'
        data = {"id":1,"method":"get_account_by_name","params":[self.default_name]}
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        account_id = response.json()["result"]["id"]
        
        values = {"name":self.default_name,
                  "smartcoins_id":self.default_smartcoins_id.id,
                  "user_assets_id":self.default_user_assets_id.id,
                "block_trade_coin_ids" : [(6,0, block_trade_coins_ids_list)],
                  "popup_shown":True,
                  "num_of_loyalty_rps" : self.loyalty_rps,
                  "eq_amount_loyalty_rps" : self.loyalty_rps_equivalent,
                  "wifkey": self.default_wifkey,
                  "user_account_id": account_id}
        
    

        rec = self.env['smartcoins_pos.smartcoins_pos'].search([("id","=",1)])
        if rec:
            rec.write(values)
        else:
            self.env['smartcoins_pos.smartcoins_pos'].create(values)
    
    
    @api.model
    def _get_loyalty_rps(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            return rec[0]['num_of_loyalty_rps']
        return ""
    
    @api.model
    def _get_loyalty_rps_equivalent(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            return rec[0]['eq_amount_loyalty_rps']
        return ""
    
    @api.model
    def _get_name(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            return rec[0]['name']
        return ""
    
    @api.model
    def _get_user_assets_id(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            return rec[0]['user_assets_id']
        return ""
    @api.model
    def _get_smartcoins_id(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            return rec[0]['smartcoins_id']
        else:
            selected_currency = self.env.user.company_id.currency_id.name
            rec = self.env['smartcoins_pos.smartcoins'].search([("name","like",selected_currency)])
            if rec:
                return [rec.id]
        return ""

    @api.model
    def _get_bt_smartcoins_ids(self):
        rec = self.env['smartcoins_pos.bt_smartcoins'].search([])
        return rec
    
    @api.model
    def _get_popup_shown(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            if rec[0]['popup_shown'] == True:
                return True
        return False
    
    def on_change_loyalty_data(self,cr,user,ids, default_user_assets_id,
                               loyalty_rps, loyalty_rps_equivalent, context=None):
        res = {
            'value': {
                    'loyalty_pts_label': "",
              }
        }
        
        if default_user_assets_id and default_user_assets_id != "" and \
            loyalty_rps != "" and \
            loyalty_rps_equivalent != "":
            currency_symbol = self.pool['res.users'].browse(cr, user, user, context=context).company_id.currency_id.symbol
            loyalty_reward_name = self.pool['smartcoins_pos.user_assets'].browse(cr, user, default_user_assets_id, context=context).name
            
            res["value"]["loyalty_pts_label"] = str(loyalty_rps) + " " + loyalty_reward_name + \
            " for every " + currency_symbol + str(loyalty_rps_equivalent) + " spent (over any timeframe)." 
            
        return res
    
    @api.model
    def _get_wifkey(self):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
        if rec:
            return rec[0]['wifkey']
        return ""