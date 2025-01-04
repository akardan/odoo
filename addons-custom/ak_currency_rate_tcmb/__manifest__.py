{
    'name': 'TCMB Exchange Rate Update',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Fetch and update exchange rates from TCMB',
    'author': 'Kardan.Digital',
    'website': 'http://kardan.digital',
    'license': 'LGPL-3',
    'depends': ['base', 'account'],
    'data': [
        'data/cron_jobs.xml',
        'views/view_currency_tree_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
