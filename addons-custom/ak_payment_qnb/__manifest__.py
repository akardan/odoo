{
    'name': 'QNB Payment Provider',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Integrate QNB Payment Gateway with Odoo',
    'description': """
        This module integrates the QNB Payment Gateway with Odoo, allowing for seamless payment processing.
    """,
    'author': 'Kardan.Digital',
    'website': "https://kardan.digital",
    'depends': ['base', 'payment'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_qnb_templates.xml',
        'views/payment_provider_views.xml',
        
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
