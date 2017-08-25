# -*- coding: utf-8 -*-

from openerp import models, fields, api
import requests, json
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class assets_fetch(models.Model):
    _name = 'smartcoins_pos.assets_fetch'    

    def fetchAssets(self,cr):
        assets = getAllAssets()
        activeAssets = getActiveAssets(assets)
        for smartCoin in activeAssets['smartCoins']:
            values = {"name":smartCoin['symbol'],'asset_id':smartCoin['id'], 'description':smartCoin['options']['description'], 'is_smart_coin':True}
            asset_id = self.pool.get("smartcoins_pos.smartcoins").search(cr, 1, [('asset_id','=',smartCoin['id'])], context=None)
            if not asset_id:
                self.pool.get('smartcoins_pos.smartcoins').create(cr,1,values)
        for userIssuedAsset in activeAssets['userIssuedAssets']:
            values = {"name":userIssuedAsset['symbol'],'asset_id':userIssuedAsset['id'], 'description':userIssuedAsset['options']['description'], 'is_smart_coin':False}
            asset_id = self.pool.get("smartcoins_pos.user_assets").search(cr, 1, [('asset_id','=',userIssuedAsset['id'])], context=None)
            if not asset_id:
                self.pool.get('smartcoins_pos.user_assets').create(cr,1,values)
                
    def fetch_block_trade_coins(self, cr):
        btCoins = getBlockTradeCoins()
        for smCoin in btCoins:
            if smCoin['coinType'] not in ["muse", "bts"] and smCoin['walletType'] != "bitshares2": 
                values = {'name':smCoin['name'],
                          'coin_type':smCoin['coinType'], 
                          'symbol': smCoin['symbol'],
                          'wallet_type': smCoin['walletType'],
                        'transaction_fee': smCoin['transactionFee'],
                        'precision': smCoin['precision'],
                        'backing_coin_type': smCoin['backingCoinType']}
                symbol = self.pool.get("smartcoins_pos.bt_smartcoins").search(cr, 1, [('symbol','=',smCoin['symbol'])], context=None)
                if not symbol:
                    self.pool.get('smartcoins_pos.bt_smartcoins').create(cr,1,values)
    
def getBlockTradeCoins():
    url = 'https://blocktrades.us/api/v2/coins'
    response = requests.get(url, verify=False)
    return response.json()
        
def getAllAssets(data="A"):
    url = 'https://bitshares.openledger.info/ws/'
    data = {"id":2,"method":"list_assets","params":[data,100]}
    headers = {'content-type': 'application/json'}           
    response = requests.post(url, data=json.dumps(data), headers=headers)
    json_data = json.loads(response.text)
    results = json_data['result']
    if len(results) > 1:
        results += getAllAssets(results[-1]['symbol'])
    return results

def getActiveAssets(assets):
    smartCoins = []
    userIssuedAssets = []
    for asset in assets:
        baseAmount = asset['options']['core_exchange_rate']['base']['amount']
        quoteAmount = asset['options']['core_exchange_rate']['quote']['amount']
        if baseAmount == 0 or quoteAmount == 0:
            continue
        holders = getHolders(asset['symbol']) or 0;
        if "bitasset_data_id" in asset and asset['issuer'] == "1.2.0" and holders > 0:
            settlement_fund = getSettlementFund(asset['bitasset_data_id'])
            if settlement_fund == 0:
                smartCoins.append(asset)
        elif holders > 3:
            userIssuedAssets.append(asset)
    return dict(smartCoins = smartCoins,userIssuedAssets = userIssuedAssets)

def getHolders(symbol):
    url = 'http://cryptofresh.com/api/holders?asset=%s' % symbol
    response = requests.get(url)
    json_data = json.loads(response.text)
    return len(json_data)

def getSettlementFund(bitasset_data_id):
    url = 'https://bitshares.openledger.info/ws/'
    data = {"id":2,"method":"get_objects","params":[[bitasset_data_id]]}
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    json_data = json.loads(response.text)
    return json_data['result'][0]['settlement_fund']

def getExchangeRate(baseAssetId, quoteAssetId):
    url = 'https://bitshares.openledger.info/ws/'
    data = {"id":1,"method":"get_limit_orders","params":[baseAssetId, quoteAssetId, 1]}
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    result = response.json()["result"]
    baseAmount = float(result[1]["sell_price"]["quote"]["amount"])
    quoteAmount = float(result[1]["sell_price"]["base"]["amount"])
    
    url = 'https://bitshares.openledger.info/ws/'
    data = {"id":1,"method":"get_assets","params":[[baseAssetId, quoteAssetId]]}
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    assetResult = response.json()["result"]

    basePrecision = 10**int(assetResult[0]["precision"])
    quotePrecision = 10**int(assetResult[1]["precision"])
    
    exchangeRate = float((quoteAmount/quotePrecision)/(baseAmount/basePrecision))
    return exchangeRate
