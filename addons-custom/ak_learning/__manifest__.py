# -*- coding: utf-8 -*-
{
    'name': "ak_learning Expansions",

    'summary': "Expansions for e-learning and certification exams",

    'description': """
This module enables random ordering of questions in Odoo 18 CE certification exams.
    
    Features:
    - Add course field to event that allows selecting a course for the event
    - Add a server action to set event attendees as course participants
    - Display questions in a shuffled order
    - Different question order for each user
    - Question shuffling in addition to random question selection by section
    """,

    'author': "Kardan.Digital",
    'website': "https://kardan.digital",
    'license': 'OPL-1',

    # Categories can be used to filter modules in modules listing
    'category': 'Website/eLearning',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'event',
        'website_slides',
        'website_sale',
        'website_sale_slides',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/event_views.xml',
        'views/website_slides_templates.xml',
    ],
    
    # 'assets': {
    #     'web.assets_backend': [
    #         'ak_learning/static/src/js/survey_shuffle.js',
    #     ],
    #     'web.assets_frontend': [
    #         'ak_learning/static/src/js/survey_shuffle.js',
    #     ],
    # },
    
    'installable': True,
    'application': False,
    'auto_install': False,
}