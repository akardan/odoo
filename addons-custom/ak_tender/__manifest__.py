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
    'depends': ['base', 'web', 'purchase', 'stock', 'mail', 'contacts', 'product', 'portal', 'ak_workflow', 'sale'],
    'data': [
        'security/security_groups.xml',
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'data/config_data.xml',
        'data/workflow_templates.xml',
        'data/server_actions.xml',
        'data/economic_data.xml',
        'data/mail_templates.xml',
        'data/mail_notification_templates.xml',
        'views/tender_sequence.xml',
        'views/purchase_order_line_views.xml',
        'views/purchase_order_views.xml',
        'views/tender_views.xml',
        'views/portal_templates.xml',
        'views/assets.xml',
        'views/set_target_price_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/bulk_purchase_wizard_views.xml',
        'views/add_supplier_wizard_views.xml',
        'views/tender_template_views.xml',
        'views/product_views.xml',
        'views/economic_data_views.xml',
        'views/res_partner_views.xml',
        'wizards/import_hotel_wizard_views.xml',
        'wizards/import_supplier_wizard_views.xml',
        'wizards/import_sat_wizard_views.xml',
        'wizards/tender_template_selection_wizard_views.xml',
        'views/menu.xml',
        'report/vendor_comparison_report.xml',
    ],
    'demo': [
        'demo/demo.xml',
        'data/template_demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'], # Modül ikonu için
    'assets': {
        'web.assets_backend': [
            'ak_tender/static/src/css/tender.css',
        ],
        'web.assets_frontend': [
            'ak_tender/static/src/js/portal_purchase_edit.js',
        ],
    },
}