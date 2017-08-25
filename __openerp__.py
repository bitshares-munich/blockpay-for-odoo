# -*- coding: utf-8 -*-
{
    'name': "BlockPay",

    'summary': """
        BlockPay for Point of Sale""",

    'description': """
        This module will allow Point Of Sale (POS) to accept BitShares’ Smartcoins and other cryptocurrencies such as Bitcoin.
    """,

    'author': "KNYSYS LLC",
    'website': "http://www.knysys.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views.xml',
        'templates.xml',
        'security/smart_coins_security.xml',
        'security/ir.model.access.csv',
        'data/res.users.csv'
        
    ],
    'css': ['static/src/css/smartcoins.css'],
    'qweb': ['static/src/xml/smartcoins_pos.xml'],
}
