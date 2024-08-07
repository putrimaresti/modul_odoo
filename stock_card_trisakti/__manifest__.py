# -*- coding: utf-8 -*-
{
    'name': "Stock Card Trisakti",

    'summary': """
        All warehouse related PDF and Excel reports""",

    'description': "User is able to print Pdf and Excel report of Stock move,"
                   "Product,Stock valuation.All warehouse related PDF"
                   "and Excel report",

    'author': "Trisakti University",
    'website': "Trisakti University",

    # Categories can be used to filter modules in modules listing
    'category': 'Inventory',
    'version': '16.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'stock_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_valuation_report_views.xml',
        'wizards/stock_move_report_views.xml',
        'report/ir_action_reports.xml',
        'report/stock_valuation_report_templates.xml',
        'report/stock_transfer_report_templates.xml',
        'report/stock_move_report_templates.xml',
        'report/stock_product_report_templates.xml',
        'wizards/stock_product_report_views.xml',
        'wizards/stock_transfer_report_views.xml',
        'views/warehouse_reports_menus.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets':
        {
            'web.assets_backend': [
                'stock_card_trisakti/static/src/js/stock_excel_report.js'
            ],
        },
    'images': [
        'static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
