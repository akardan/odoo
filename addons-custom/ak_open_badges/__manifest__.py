# -*- coding: utf-8 -*-
{
    'name': 'Digital Certificates & Badges',
    'version': '18.0.1.0',
    'category': 'Website',
    'sequence': -220,
    'summary': 'Digital certificates and badges management system',
    'description': """
        Digital certificates and Open Badges management system
        * Create and manage Open Badge templates
        * Issue digital certificates and badges
        * Verify certificates through QR codes
        * Integration with events and courses
        * Open Badges 2.0 compliant
    """,
    'author': "Kardan.Digital",
    'website': "https://kardan.digital",
    'license': 'LGPL-3',

    # Bu modülün çalışması için gerekli olan bağımlılıklar
    'depends': ['base', 'mail','web','event','website_event','website_slides','contacts'],  

    # Her zaman yüklenecek veriler
    'data': [
        # Güvenlik ve Erişim Hakları
        'security/open_badges_security.xml',  # Güvenlik grupları
        'security/ir.model.access.csv',       # Model erişim hakları
        
        # Master Data ve Konfigürasyon
        'data/badge_sequence.xml',           # Sertifika numaralandırma
        'data/badge_type_data.xml',          # Rozet tipleri
        'data/certificate_template.xml',     # Hazır şablonlar
        
        # Views ve Menüler
        'views/badge_issuer_views.xml',      # Veren kurum görünümleri
        'views/badge_class_views.xml',       # Badge sınıf görünümleri
        'views/badge_assertion_views.xml',   # Assertion görünümleri
        'views/badge_tag_views.xml',         # Tag görünümleri
        'views/menu_views.xml',              # Menü yapısı
        
        # Raporlar
        'reports/badge_reports.xml',        # Önce report tanımları

        'views/templates.xml',               # Website şablonları
        
        # Email Şablonları
        'data/mail_template_data.xml',       # E-posta şablonları
    ],

    'assets': {
        'web.assets_backend': [
            'ak_open_badges/static/src/css/verification.css',
            'ak_open_badges/static/src/scss/certificate_style.scss',
        ],
    },

    # Demo modu için gerekli veriler (isteğe bağlı)

    # Modül kurulum özellikleri
    'installable': True,
    'application': True,
    'auto_install': False,
}
