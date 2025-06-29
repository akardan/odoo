{
    'name': 'AK Workflow - Advanced Generic Workflow Engine',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Advanced Workflow Engine based on OCA Tier Validation',
    'description': '''
        AK Workflow - Generic Multi-Model Workflow Engine
        =================================================
        
        OCA base_tier_validation modülü üzerine kurulmuş gelişmiş workflow sistemi:
        
        ✓ Generic çoklu model desteği
        ✓ Dinamik state ve transition tanımları  
        ✓ Gelişmiş action sistemi (Email, Method, Webhook, vs.)
        ✓ Tier validation entegrasyonu
        ✓ Python tabanlı koşullu geçişler
        ✓ Workflow tasarım arayüzü
        ✓ SAP entegrasyonu hazır
        ✓ İLKO satın alma grupları için özel şablonlar
        ✓ Analytics ve dashboard
        
        İLKO Satın Alma Grupları Desteği:
        • Direkt Satın Alma Workflow'u
        • Endirekt Satın Alma Workflow'u  
        • MICE İhale Workflow'u
        • Promosyon İhale Workflow'u
    ''',
    'author': "Kardan.Digital",
    'website': "https://www.kardan.digital",
    'depends': [
        'base_tier_validation',  # OCA modülü - ZORUNLU
        'base',
        'mail',
        'web',
        'portal',  # Portal desteği için
    ],
    'external_dependencies': {
        'python': ['requests']  # Webhook desteği için
    },
    'data': [
        # Data
        'data/mail_templates.xml',
        
        # Views
        'views/ak_workflow_views.xml',
        'views/workflow_designer_views.xml',
        'views/tier_validation_extend_views.xml',
        'views/workflow_dashboard_views.xml',

        # Security (after views to ensure models are loaded)
        'security/ir.model.access.csv',
        'security/workflow_security.xml',
        
        # Wizards
        'wizards/workflow_designer_wizard.xml',
        'wizards/bulk_transition_wizard.xml',
        'wizards/workflow_import_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ak_workflow/static/src/js/workflow_widget.js',
            'ak_workflow/static/src/js/workflow_designer.js', 
            'ak_workflow/static/src/js/workflow_dashboard.js',
            'ak_workflow/static/src/css/workflow.css',
            'ak_workflow/static/src/css/workflow_designer.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 100,
}