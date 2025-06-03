# -*- coding: utf-8 -*-
{
    'name': "İhale",
    'summary': """
        ERP entegrasyonlu ve çok aşamalı ihale yönetimi modülü prototipi.
    """,
    'description': """
        Bu modül,  çok aşamalı satın alma ihale süreçlerini Odoo üzerinde yönetmek için tasarlanmıştır.
        - ERP Entegrasyon (simülasyon)
        - Çok Aşamalı İhale Süreci (1. Teklif Toplama, Hedef Fiyat, 2. Teklif Toplama)
        - Tedarikçi Portal Entegrasyonu (veri girişi temsili)
        - Onay Mekanizması entegrasyonu (Approvals modülü ile)
        - Raporlama ve Analiz altyapısı
        - İhale Kalemleri yönetimi
        - Odoo'nun temel satın alma (purchase.order) modülü ile entegrasyon simülasyonu.
    """,
    'author': "Kardan.Digital",
    'website': "https://www.kardan.digital",
    'category': 'Purchases',
    'version': '0.5', # Versiyon yükseltildi
    'sequence': -225,
    'depends': ['base', 'purchase', 'stock', 'mail', 'contacts', 'product', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'views/tender_sequence.xml',
        'views/tender_result_line_views.xml',
        'views/tender_result_views.xml',
        'views/tender_views.xml',
        'views/portal_templates.xml',
        'views/set_target_price_wizard_views.xml',
        'wizards/tender_action_wizard_views.xml',
        'wizards/tender_approval_info_wizard_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'], # Modül ikonu için
}