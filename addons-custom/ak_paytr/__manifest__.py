{
    'name': 'PayTR Payment Provider',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'PayTR iFrame API Integration for Payments',
    'description': """
        Integrates PayTR iFrame API with Odoo eCommerce.
        Allows secure credit card payments.
    """,
    'author': 'Kardan.Digital',
    "website": "https://kardan.digital",
    'depends': ['base', 'website_sale', 'payment'],
    'data': [
        'views/payment_paytr_templates.xml',
        'views/paytr_payment_view.xml',
        
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
}