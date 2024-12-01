# -*- coding: utf-8 -*-
{
    'name': "Reference Price Tracking",  # Modül adı
    'version': '18.0.1.0',
    'sequence': -210,
    'summary': "A module for tracking reference prices for market access departments.",  # Modülün kısa özeti
    'description': """
This module allows users to track reference prices for products in various countries and markets.
It supports the management of historical price changes, country-specific price mappings, and automated notifications for price updates.
    """,  # Modülün uzun açıklaması

    'author': "Kardan.Digital",
    'website': "https://kardan.digital",

    # Modül kategorisi (Daha spesifik bir kategori kullanılıyor)
    'category': 'Sales Management',
 
    # Bu modülün çalışması için gerekli olan bağımlılıklar
    'depends': ['base', 'sale', 'mail'],  # Temel modüller, satış ve mail modülleri bağımlı

    # Her zaman yüklenecek veriler
    'data': [
        'security/security.xml',  # Güvenlik ve erişim hakları tanımları
        'security/ir.model.access.csv',  # Güvenlik ve erişim hakları tanımları
        'data/res_partner_industry_data.xml',        
        'data/product_pharma_attributes_data.xml',
        'wizards/country_import_wizard_view.xml',
        'views/menu.xml',
        'views/res_country_titck_code_view.xml',
        'views/res_partner_view.xml',
        'views/product_template_view.xml',
        'views/product_pharma_attributes_views.xml',
        # 'data/ir_cron_data.xml',  # Zamanlanmış görevler (fiyat güncelleme takipleri için)
    ],

    # Demo modu için gerekli veriler (isteğe bağlı)
    'demo': [
        # 'demo/demo.xml',
    ],

    # Modül kurulum özellikleri
    'installable': True,
    'application': True,
    'auto_install': False,
}
