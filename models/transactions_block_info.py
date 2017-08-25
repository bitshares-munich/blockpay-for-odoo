# -*- coding: utf-8 -*-

from openerp import models, fields, api
import requests, json
from assets_fetch import getExchangeRate

class smartcoinsTransactionsInfo(models.Model):
    _name = 'smartcoins_pos.transactions_block_info'
    
    user_id = fields.Char()
    amount = fields.Float()
    asset_id = fields.Char()
    isProcessTransaction = fields.Boolean(string='')
    isRewardPointAsset = fields.Boolean(string='')
    order_id = fields.Char()
    
    @api.model
    def get_paid_amount(self, order_id):
        rec = self.env['smartcoins_pos.transactions_block_info'].search_read([("order_id","=",order_id)])
#         print "----Order Id: ", order_id
#         print "----Record", len(rec), rec
        if rec:
            selected_data = {}
            if len(rec) == 1:
                selected_data['order_payment_amount'] = rec[0]["amount"]
            else:
                settings_rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])

                if settings_rec:
#                     selected smartcoin
                    rec_selected_smartcoin = self.env['smartcoins_pos.smartcoins'].search_read([("id","=",settings_rec[0]['smartcoins_id'][0])])
#                     selected user issued asset
                    rec_selected_uia = self.env['smartcoins_pos.user_assets'].search_read([("id","=",settings_rec[0]['user_assets_id'][0])])
#                     User issued asset id
                    selected_uia_id = rec_selected_uia[0]["asset_id"];
                    selected_uia_symbol = rec_selected_uia[0]["name"];
#                     smart coin id
                    selected_asset_id = rec_selected_smartcoin[0]["asset_id"]
                                        
                    selected_data['transactions'] = []
                    for r in rec:
                        if r["isRewardPointAsset"] and r["asset_id"] == selected_uia_id:
                            rp_rate = getExchangeRate(selected_asset_id, r["asset_id"])
                            r["rp_amount"] = (r["amount"])
                            r["amount"] = ( r["amount"] / rp_rate)
                            r["symbol"] = selected_uia_symbol;
                            lst = selected_data['transactions']
                            lst.append(r)
                        else:
                            lst = selected_data['transactions']
                            lst.append(r)
            return selected_data
        return ""
    
    @api.model
    def store_transaction_info(self,block, order):
        rec = self.env['smartcoins_pos.smartcoins_pos'].search_read([("id","=",1)])
#        Must have wifkey, from_account, to_account, amount, asset_symbol
        if rec:
            rec_selected_smartcoin = self.env['smartcoins_pos.smartcoins'].search_read([("id","=",rec[0]['smartcoins_id'][0])])
            rec_selected_uia = self.env['smartcoins_pos.user_assets'].search_read([("id","=",rec[0]['user_assets_id'][0])])
            selected_asset_id = rec_selected_smartcoin[0]["asset_id"]
            selected_uia_symbol = rec_selected_uia[0]["name"]
            selected_uia_id = rec_selected_uia[0]["asset_id"];
            merchant_account_id = rec[0]['user_account_id'] 
            wifkey = rec[0]['wifkey']
            eq_amount_loyalty_rps = rec[0]['eq_amount_loyalty_rps']
            num_of_loyalty_rps = rec[0]['num_of_loyalty_rps']

            operations = get_transaction(block)["result"]["transactions"][0]["operations"]
            for opr in operations:
                row = opr[1]
#       row.to = "Merchant Account"
#       row.amount.asset_id = "Select Smartcoin id"
                if row["to"] == merchant_account_id and (row["amount"]["asset_id"] == selected_asset_id or 
                                                          row["amount"]["asset_id"] == selected_uia_id):
                    asset_precision = get_asset(row["amount"]["asset_id"])["result"][0]["precision"]
                    values = {"user_id" : row["from"],
                              "amount" : row["amount"]["amount"] / 10 ** float(asset_precision),
                              "asset_id": row["amount"]["asset_id"],
                              "isProcessTransaction": False,
                              "order_id": order }
                    if row["amount"]["asset_id"] == selected_uia_id:
                        values["isRewardPointAsset"] = True
                    else:
                        values["isRewardPointAsset"] = False
                    rps_receiver = row["from"]
                    rec_id = self.env['smartcoins_pos.transactions_block_info'].create(values)
                    #Transferring Fees
                    openpos_fee = 0.6
                    openpos_amount = "%.4f" % (values["amount"] * openpos_fee / 100)
                    btmunich_fee = 0.3
                    btmunich_amount = "%.4f" % (values["amount"] * btmunich_fee / 100)
                    result1 = transfer_reward_points(wifkey, merchant_account_id, "openpos", openpos_amount, values["asset_id"])
                    result2 = transfer_reward_points(wifkey, merchant_account_id, "bitshares-munich", btmunich_amount, values["asset_id"])
                    
            rec_for_process_rps = self.env['smartcoins_pos.transactions_block_info'].search_read([("isProcessTransaction","=",False),
                                                                                    ("isRewardPointAsset","=",False), 
                                                                                    ("user_id","=",rps_receiver)])
            if rec_for_process_rps:
                sum = 0
                rec1Ids = []
                for r in rec_for_process_rps:
                    sum += r["amount"]
                    rec1Ids.append(r["id"])
                rec1set = self.env['smartcoins_pos.transactions_block_info'].browse(rec1Ids)
                remainBalanceSet = self.env['smartcoins_pos.user_balance'].search_read([("user_id","=",rps_receiver)])
                if remainBalanceSet:
                    remainingBalanceBrowse = self.env['smartcoins_pos.user_balance'].browse([remainBalanceSet[0]["id"]])
                    sum += remainBalanceSet[0]['remaining_balance']
                #Transferring Reward Points
                if sum >= eq_amount_loyalty_rps:
                    remaining_balance = sum % eq_amount_loyalty_rps;
                    sum -= remaining_balance
                    loyalty_pts_given = (sum / eq_amount_loyalty_rps) * num_of_loyalty_rps
                    result = transfer_reward_points(wifkey, merchant_account_id, rps_receiver, int(loyalty_pts_given), selected_uia_symbol)
                    print "----Transfer result: ", result["status"]
                    if result["status"] != "failure":
                        values = {"user_id": rps_receiver, "remaining_balance" : remaining_balance}
                        updateTransactionInfoValues = {"isProcessTransaction": True};
                        if remainBalanceSet:
                            remainingBalanceBrowse.write(values)
                            rec1set.write(updateTransactionInfoValues)
                        else:
                            self.env['smartcoins_pos.user_balance'].create(values)
                            rec1set.write(updateTransactionInfoValues)
                
def transfer_reward_points(wifkey, from_account, to_account, amount, asset_symbol):
    print "------Sending reward points"
    url = 'http://188.166.147.110:9000'
    data = {"method": "transfer", 
            "wifkey": wifkey, 
            "from_account" : from_account, 
            "to_account": to_account, 
            "amount" : amount, "asset_symbol" : asset_symbol}
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()

def get_transaction(block):
    url = 'https://bitshares.openledger.info/ws/'
    data = {"id":1,"method":"get_block","params":[block]}
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()

def get_asset(asset_id):
    url = 'https://bitshares.openledger.info/ws/'
    data = {"id":1,"method":"get_assets","params":[[asset_id]]}
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()