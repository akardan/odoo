# -*- coding: utf-8 -*-
{
    'name': "ak_exams",
    'summary': "Exam Management System for Exam Providers",
    'description': """
Exam Management System for customers that isolates based on company
Özellikler:
        - Yerleşik Odoo API Key yönetimi
        - Takım kodu ve hiyerarşi alanları
        - API ile satış ekibi hiyerarşisi senkronizasyonu
 """,

    'author': "Kardan.Digital",
    'website': "https://kardan.digital",

    'category': 'Marketing/Surveys',
    'version': '18.0.1.0',
        
    'sequence': -225,

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'survey',
        'crm',
        'mail',
        'website', # Added website dependency
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/survey_security.xml',
        'security/survey_question_poll_security.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/survey_exam_features_view.xml',
        'views/survey_full_screen_template.xml',
        'views/survey_question_poll_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ak_exams/static/src/scss/ak_exams_survey.scss',
            'ak_exams/static/src/js/survey_security_minimal.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

