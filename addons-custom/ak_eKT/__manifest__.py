{
    'name': 'Digital Prospectus Management (e-KT Hub)',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Pharmaceutical',
    'summary': 'Elektronik Kullanma Talimatı ve Dijital Prospektüs Yönetimi',
    'description': '''
    Dijital Prospektüs Yönetimi Modülü
    ================================
    
    Bu modül ilaç ve sağlık sektörü için dijital prospektüs yönetimi sağlar:
    
    * Elektronik Kullanma Talimatı (e-KT) yönetimi
    * QR kod tabanlı erişim sistemi
    * Paket bazlı hizmet yönetimi (S/M/L/XL)
    * KVKK uyumlu güvenli veri saklama
    * Çoklu dil desteği
    * AI seslendirme entegrasyonu
    * Kullanım raporlama ve analitik
    * Tedarikçi/eczane portalı
    ''',
    'author': 'Kardan.Digital',
    'website': 'https://kardan.digital',
    'depends': [
        'base',
        'website',
        'mail',
        'portal',
        'sale',
        'stock',
        'account',
        'contacts'
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/service_packages.xml',
        'data/email_templates.xml',
        
        # Views
        'views/prospectus_views.xml',
        'views/service_package_views.xml',
        'views/usage_analytics_views.xml',
        'views/customer_portal_views.xml',
        'views/menu_items.xml',
        
        # Website Templates
        'templates/prospectus_public.xml',
        'templates/customer_portal.xml',
        
        # Reports
        'reports/usage_report.xml',
        'reports/analytics_report.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ak_eKT/static/src/css/backend.css',
            'ak_eKT/static/src/js/qr_generator.js',
        ],
        'web.assets_frontend': [
            'ak_eKT/static/src/css/frontend.css',
            'ak_eKT/static/src/js/frontend.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}