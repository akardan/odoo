{
    'name': 'Superset Analytics Integration',
    'version': '16.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Embed Apache Superset dashboards with SSO authentication',
    'description': """
        Superset Analytics Integration
        ============================
        
        This module provides seamless integration between Odoo and Apache Superset:
        
        * Embed Superset dashboards directly in Odoo
        * Single Sign-On (SSO) authentication via JWT
        * Role-based access control
        * Automatic token refresh
        * Responsive iframe integration
        
        Perfect for business intelligence and advanced analytics needs.
    """,
    'author': 'kardan.digital',
    'website': 'https://kardan.digital',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/superset_dashboard_views.xml',
        'views/menu_items.xml',
    ],
    'external_dependencies': {
        'python': ['PyJWT'],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}