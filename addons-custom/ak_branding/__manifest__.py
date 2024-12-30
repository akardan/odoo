{
    'name': 'AK Branding',
    'version': '1.0',
    'summary': 'Dynamic branding customization for Powered by Kardan.Digital',
    'author': 'Kardan.Digital',
    'depends': ['base', 'web'],
    'data': [
        'views/branding_views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            '/ak_branding/static/src/scss/style.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
}
