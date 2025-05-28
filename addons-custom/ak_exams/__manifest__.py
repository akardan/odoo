# -*- coding: utf-8 -*-
{
    'name': "ak_exams",
    'summary': "Exam Management System for customers",
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

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'survey',
        'crm',
        'mail',
    ],

    # always loaded
    'data': [
        'security/survey_security.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ak_exams/static/src/scss/ak_exams_survey.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

