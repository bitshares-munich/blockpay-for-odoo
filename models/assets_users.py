# -*- coding: utf-8 -*-

from openerp import models, fields, api

class user_assets(models.Model):
    _name = 'smartcoins_pos.user_assets'
    _rec_name = 'title'

    name = fields.Char()
    asset_id = fields.Char()
    description = fields.Text()
    title = fields.Char(compute="_compute_title")

    def _compute_title(self):
        for user_asset in self:
            desc = (user_asset.description[:40] + '...') if len(user_asset.description) > 40 else user_asset.description
            user_asset.title = user_asset.name + " (" + desc + ")"
