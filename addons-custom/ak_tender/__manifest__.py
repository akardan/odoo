# -*- coding: utf-8 -*-
{
    'name': "İhale",
    'summary': """
        Çok aşamalı ihale yönetimi modülü.
    """,
    'description': """
        Çok aşamalı satın alma ihale süreçlerini Odoo üzerinde yönetmek için tasarlanmış gelişmiş ihale yönetim modülü.
        
        Özellikler:
        - İş Akışı (Workflow) Yönetimi: Esnek, çok aşamalı ihale süreç yönetimi
        - ERP Entegrasyonu: Satın alma modülü ile tam entegrasyon
        - Çok Aşamalı İhale Süreci: 1. Teklif Toplama, Hedef Fiyat Belirleme, 2. Teklif Toplama
        - Tedarikçi Portal: Tedarikçilerin teklif girişi ve takibi
        - Otomatik Durum Geçişleri: Deadline bazlı otomatik süreç yönetimi
        - Onay Mekanizması: Çoklu onay süreçleri ve yetkilendirme
        - Gelişmiş Raporlama: Tedarikçi karşılaştırma ve analiz araçları
        - İhale Kalemleri: Detaylı ürün ve satır bazlı teklif yönetimi
        - E-posta Entegrasyonu: Otomatik bildirimler ve takip sistemi
    """,
    'author': "Kardan.Digital",
    'website': "https://kardan.digital",
    'category': 'Purchases',
    'version': '0.5', # Versiyon yükseltildi
    'sequence': -225,
    'depends': ['base', 'web', 'purchase', 'purchase_requisition', 'stock', 'mail', 'contacts', 'product', 'portal', 'ak_workflow', 'sale', 'product_matrix', 'ak_ai'],
    'data': [
        'security/security_groups.xml',
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'data/config_data.xml',
        'data/workflow_templates.xml',
        'data/server_actions.xml',
        'data/purchase_order_server_actions.xml',
        'data/economic_data.xml',
        'data/tender_type_rules_data.xml',
        'data/mail_templates.xml',
        'data/automation_rules.xml',
        'data/tender_cron.xml',
        'data/mail_notification_templates.xml',
        'data/email_import_cron.xml',
        'data/payment_terms_data.xml',
        'data/supplier_application_sequence.xml',
        'data/supplier_application_mail_templates.xml',
        'views/supplier_application_views.xml',
        'views/supplier_registration_templates.xml',
        'wizards/supplier_application_reject_wizard_views.xml',
        'views/tender_sequence.xml',
        'views/purchase_order_line_views.xml',
        'views/purchase_order_views.xml',
        'views/tender_views.xml',
        'views/portal_templates.xml',
        'views/assets.xml',
        'views/res_config_settings_views.xml',
        'views/bulk_purchase_wizard_views.xml',
        'views/add_supplier_wizard_views.xml',
        'views/tender_template_views.xml',
        'views/product_views.xml',
        'views/economic_data_views.xml',
        'views/res_partner_views.xml',
        'views/tender_type_rules_views.xml',
        'wizards/import_hotel_wizard_views.xml',
        'wizards/import_supplier_wizard_views.xml',
        'wizards/import_sat_wizard_views.xml',
        'wizards/import_historical_po_wizard_views.xml',
        'wizards/tender_template_selection_wizard_views.xml',
        'wizards/tender_transfer_lines_wizard_views.xml',
        'views/purchase_requisition_views.xml',
        'wizards/import_sat_to_pool_wizard_views.xml',
        'views/menu.xml',
        'views/move_tender_lines_wizard_views.xml',
        'report/vendor_comparison_report.xml',
    ],
    'demo': [
        'demo/demo.xml',
        'data/template_demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'images': ['static/description/icon.png'], # Modül ikonu için
    'assets': {
        'web.assets_backend': [
            'ak_tender/static/src/css/tender.css',
            'ak_tender/static/src/js/tender_product_field.js',
            'ak_tender/static/src/js/tender_product_field.xml',
        ],
        'web.assets_frontend': [
            'ak_tender/static/src/js/portal_purchase_edit.js',
        ],
    },
}