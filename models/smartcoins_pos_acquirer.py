# -*- coding: utf-8 -*-

from openerp import models, fields, api


class smartcoins_pos_account_journal(models.Model):
    _inherit = 'account.journal'

    smartcoins_pos_id = fields.Many2one('smartcoins_pos.smartcoins_pos', string='Smartcoins Gateway', help='The SmartCoins Account used for this Journal')

