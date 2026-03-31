# -*- coding: utf-8 -*-
{
    'name': "MICE İhale Yönetimi",
    'summary': """
        Meeting, Incentive, Conference, Event ihaleleri için senaryo bazlı yönetim.
    """,
    'description': """
        ak_tender modülünü MICE organizasyon ihaleleri için genişleten modül.

        Özellikler:
        - Senaryo bazlı ihale yönetimi (otel + pansiyon + tarih kombinasyonları)
        - Alternatif tarih seçenekleri (sezon farkı, maliyet çarpanı)
        - Çok turlu kısa liste (shortlist) mekanizması
        - Tedarikçi karşı teklif (counter-proposal) desteği
        - NPV bazlı fiyat karşılaştırma (ödeme vadesi iskonto)
        - MICE özel ihale kalemleri (konaklama, transfer, F&B, teknik, uçuş)
        - Senaryo oluşturma ve eleme sihirbazları
        - Sonraki tur başlatma iş akışı

        İhale Hiyerarşisi:
        ak.tender (MICE tipi)
          └── ak.tender.scenario   → "Titanic Beach 5★ Antalya - HB"
                ├── ak.tender.scenario.date  → "2-4 Kasım (Düşük Sezon)"
                ├── ak.tender.scenario.date  → "9-11 Kasım (Yüksek Sezon)"
                └── ak.tender.line  → Konaklama, Transfer, F&B kalemleri
    """,
    'author': "Kardan.Digital",
    'website': "https://kardan.digital",
    'category': 'Purchases',
    'version': '1.1',
    'sequence': -224,

    # ak_tender'a bağımlı — ak_tender kuruluysa otomatik görünür
    'depends': ['ak_tender'],

    'data': [
        # Güvenlik — her zaman ilk
        'security/security_groups.xml',
        'security/security_rules.xml',
        'security/ir.model.access.csv',

        # Seed data — model kurulduktan sonra yüklenir
        'data/scenario_types.xml',

        # Görünümler
        'views/tender_scenario_views.xml',
        'views/tender_scenario_line_views.xml',
        'views/tender_mice_views.xml',
        'views/portal_mice_templates.xml',

        # Sihirbazlar
        'wizards/tender_scenario_wizard_views.xml',
        'wizards/add_packages_wizard_views.xml',

        # Menü — her zaman en son
        'views/menu.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'ak_tender_mice/static/src/css/kanban_style.css',
        ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
