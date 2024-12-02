{
    'name': 'Sale Subscription',
    'version': '18.0.1.0',
    'summary': 'This module enables subscription for Products',
    "author": "Silver Touch Technologies Limited",
    "website": "https://www.silvertouch.com",
    'category': 'Sales',
    'depends': [
        'sale_management','product','stock', 'sale_pdf_quote_builder'
    ],
    'data': [
        "data/email_template.xml",
        "data/notification_cron.xml",
        "data/close_reason_data.xml",
        "security/ir.model.access.csv",
        "views/subscription_views.xml",
        'views/product_views.xml',
        "views/sale_views.xml",
        "views/ir_cron.xml",
        "views/close_reason.xml",
        "views/res_config.xml",
        "wizard/close_reason_wizard.xml"
    ],
    'license':'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': ['static/description/banner.png'],
}
