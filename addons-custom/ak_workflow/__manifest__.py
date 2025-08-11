{
    'name': 'AK Workflow - Advanced Generic Workflow Engine',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Advanced Generic Workflow Engine',
    'license': 'OPL-1',
    'description': '''
        AK Workflow - Standalone Generic Multi-Model Workflow Engine
        ===========================================================
        
        This module provides an advanced, standalone workflow system.
        
        ✓ Generic multi-model support
        ✓ Dynamic state and transition definitions
        ✓ Advanced action system (Email, Method, Webhook, etc.)
        ✓ Conditional transitions based on Python code
        ✓ Visual workflow designer
        ✓ Analytics and dashboard
    ''',
    'author': "Kardan.Digital",
    'website': "https://www.kardan.digital",
    'depends': [
        'base',
        'mail',
        'web',
        'portal',
    ],
    'external_dependencies': {
        'python': ['requests']  # Webhook desteği için
    },
    'data': [
        'data/mail_templates.xml',
        'views/ak_workflow_definition_views.xml',
        'views/ak_workflow_state_views.xml',
        'views/ak_workflow_transition_views.xml',
        'views/ak_workflow_action_views.xml',
        'views/ak_workflow_views.xml',
        'views/workflow_designer_views.xml',
        'views/workflow_dashboard_views.xml',
        'wizards/workflow_designer_wizard.xml',
        'wizards/bulk_transition_wizard.xml',
        'wizards/workflow_import_wizard.xml',
        'wizards/workflow_transition_wizard_views.xml',
        'views/ak_workflow_menu_views.xml',
        'security/ir.model.access.csv',
        'security/workflow_security.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ak_workflow/static/src/components/workflow_button_group/workflow_button_group.js',
            'ak_workflow/static/src/components/workflow_button_group/workflow_button_group.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 100,
}