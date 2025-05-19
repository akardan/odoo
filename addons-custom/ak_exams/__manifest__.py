# -*- coding: utf-8 -*-
{
    'name': "ak_exams",

    'summary': "Exam Management System for customers",

    'description': """
Exam Management System for customers that isolates based on company
    """,

    'author': "Kardan.Digital",
    'website': "https://kardan.digital",

    'category': 'Marketing/Surveys',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['survey'],

    # always loaded
    'data': [
        'security/survey_security.xml',
        'views/views.xml',
        'views/templates.xml',
    ],

}

