# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class smartcoins(models.Model):
    _name = 'smartcoins_pos.smartcoins'
    _rec_name = 'title'

    name = fields.Char()
    asset_id = fields.Char()
    description = fields.Text()
    title = fields.Char(compute="_compute_title")

    def _compute_title(self):
        for smartcoin in self:
            smartcoin.title = "bit" + smartcoin.name + " (" + smartcoin.description + ")"
            
    def init(self,cr):
#         print "---------------init called----------"
        _logger.info("---------------init called----------")
        self.pool.get('smartcoins_pos.assets_fetch').fetchAssets(cr)
