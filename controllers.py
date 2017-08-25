# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request

class smartcoinsPos(http.Controller):
    @http.route('/smartcoins_pos/smartcoins_transactions/<order>', auth='public')
    def index(self, req, order, **kw):
        request.session.authenticate(request.session.db, 'appadmin', '123456')
        if 'block' in req.params and 'trx' in req.params:
            block = req.params.get('block')
            trx = req.params.get('trx')
            req.session.model('smartcoins_pos.smartcoins_transactions').store_transactions(order,block,trx)
            req.session.model('smartcoins_pos.transactions_block_info').store_transaction_info(block, order)
            
        return "Thank you for your payment"

#     @http.route('/smartcoins_pos/smartcoins_pos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('smartcoins_pos.listing', {
#             'root': '/smartcoins_pos/smartcoins_pos',
#             'objects': http.request.env['smartcoins_pos.smartcoins_pos'].search([]),
#         })

#     @http.route('/smartcoins_pos/smartcoins_pos/objects/<model("smartcoins_pos.smartcoins_pos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('smartcoins_pos.object', {
#             'object': obj
#         })