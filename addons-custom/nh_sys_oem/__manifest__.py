# -*- coding: utf-8 -*-
{
    'name': "ODOO RE-Branding",

    'summary': """
        Will remove ODOO branding on the system
        """,

    'description': """
        Remove all ODOO branding across the system
    """,

    'author': "NHDevTeam, Hervé",
    'website': "http://nhdevteam.com",
    'support': 'support@nhdevteam.com',
    # 'price': '10',
    # 'currency': 'EUR',

    'category': 'Technical',
    'version': '1.1',
    "license": "OPL-1",


    # any module necessary for this one to work correctly
    'depends': ['base', 'web' ],

    # always loaded
    'data': [
        'views/application_views.xml',
        'views/templates.xml',
        # 'views/res_config_settings_views.xml',
    ],
    'images' : [
        'static/description/icon.png'
    ]
}
