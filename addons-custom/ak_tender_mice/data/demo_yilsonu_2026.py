#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 Yılsonu Toplantısı — MICE Demo Veri Yükleme Scripti
========================================================

Odoo shell üzerinden çalıştırmak için:
    ./odoo-bin shell -d <veritabanı_adı> < addons-custom/ak_tender_mice/data/demo_yilsonu_2026.py

Ya da shell'e girdikten sonra:
    exec(open('addons-custom/ak_tender_mice/data/demo_yilsonu_2026.py').read())

Oluşturulan Yapı:
-----------------
İHALE: "2026 Yılsonu Toplantısı"
│
├── BÖLGE: Antalya
│   ├── OTEL A: Kaya Palazzo ★★★★★ (Belek) — TRY teklif
│   │   ├── Tarih 1: 2-5 Ocak 2026 (Düşük Sezon)
│   │   ├── Tarih 2: 9-12 Ocak 2026 (Düşük Sezon)
│   │   └── Kalemler: Double/Single/Suite oda, Transfer, Salon, Gala, Uçuş
│   └── OTEL B: Maxx Royal Belek ★★★★★ — TRY teklif
│       ├── Tarih 1: 2-5 Ocak 2026 (Düşük Sezon)
│       ├── Tarih 2: 9-12 Ocak 2026 (Düşük Sezon)
│       └── Kalemler: aynı yapı
│
└── BÖLGE: Kuzey Kıbrıs
    ├── OTEL C: Merit Crystal Cove ★★★★★ — EUR teklif
    │   ├── Tarih 1: 2-5 Ocak 2026 (Düşük Sezon)
    │   ├── Tarih 2: 9-12 Ocak 2026 (Düşük Sezon)
    │   └── Kalemler: Double/Single/Suite oda, Transfer, Salon, Gala + Uçuş (TRY)
    └── OTEL D: Elexus Hotel & Resort ★★★★★ — EUR teklif
        ├── Tarih 1: 2-5 Ocak 2026 (Düşük Sezon)
        ├── Tarih 2: 9-12 Ocak 2026 (Düşük Sezon)
        └── Kalemler: aynı yapı

Katılımcılar:
    - 100 mümessil → 50 Double oda
    - 10 yönetici  → 10 Single oda
    - 2 tepe yönetici → 2 VIP Suite oda
    Toplam: 112 kişi

Hizmetler:
    - Konaklama: Full Board (FB) — 3 gece
    - Transfer: STD (112 kişi) + VIP (2 kişi) — havalimanı ↔ otel
    - Toplantı Salonu + Teknik Ekipman — 4 gün
    - Gala Yemeği — 112 kişi × 1 akşam
    - Uçuş (TRY): İstanbul ↔ Antalya veya Kıbrıs — 112 kişi
"""

import logging
from datetime import date

_logger = logging.getLogger(__name__)

env = env  # noqa — odoo shell'de mevcut


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def get_or_create_product(name, product_type='service', uom_name=None, categ_name=None):
    """Ürünü bul ya da oluştur."""
    Product = env['product.product']
    domain = [('name', '=', name), ('type', '=', product_type)]
    product = Product.search(domain, limit=1)
    if not product:
        vals = {
            'name': name,
            'type': product_type,
            'purchase_ok': True,
            'sale_ok': False,
        }
        if uom_name:
            uom = env['uom.uom'].search([('name', 'ilike', uom_name)], limit=1)
            if uom:
                vals['uom_id'] = uom.id
                vals['uom_po_id'] = uom.id
        product = Product.create(vals)
        _logger.info('Ürün oluşturuldu: %s (ID: %s)', name, product.id)
    return product


def get_currency(code):
    """Para birimini bul."""
    currency = env['res.currency'].search([('name', '=', code)], limit=1)
    if not currency:
        raise ValueError(f'Para birimi bulunamadı: {code}')
    return currency


def get_or_create_partner(name, is_company=True, supplier_rank=1):
    """Partneri bul ya da oluştur."""
    partner = env['res.partner'].search([('name', '=', name)], limit=1)
    if not partner:
        partner = env['res.partner'].create({
            'name': name,
            'is_company': is_company,
            'supplier_rank': supplier_rank,
        })
        _logger.info('Partner oluşturuldu: %s (ID: %s)', name, partner.id)
    return partner


def get_uom(name_candidates):
    """UoM'ı birden fazla isim adayından bul."""
    for name in name_candidates:
        uom = env['uom.uom'].search([('name', 'ilike', name)], limit=1)
        if uom:
            return uom
    # Yoksa varsayılan Units döndür
    return env.ref('uom.product_uom_unit')


def get_state(name_candidates, country_code=None):
    """İl/bölgeyi bul."""
    domain = []
    if country_code:
        country = env['res.country'].search([('code', '=', country_code)], limit=1)
        if country:
            domain.append(('country_id', '=', country.id))
    for name in name_candidates:
        state = env['res.country.state'].search(domain + [('name', 'ilike', name)], limit=1)
        if state:
            return state
    return False


# ============================================================
# ANA VERİ HAZIRLAMA
# ============================================================

def create_mice_tender():
    """2026 Yılsonu MICE İhalesini oluştur."""

    print('\n' + '='*60)
    print('2026 YILSONU TOPLANTISI — MICE DEMO VERİSİ YÜKLENIYOR')
    print('='*60)

    # ---- Para Birimleri ----
    try_currency = get_currency('TRY')
    eur_currency = get_currency('EUR')

    # ---- UoM'lar ----
    uom_night = get_uom(['Gece', 'Night', 'day(s)', 'Days', 'Day'])
    uom_person = get_uom(['Kişi', 'Person', 'Unit(s)', 'Units'])
    uom_unit = env.ref('uom.product_uom_unit')
    uom_day = get_uom(['gün', 'day', 'Days', 'day(s)'])

    # ---- Ürünler ----
    print('\nÜrünler oluşturuluyor...')

    p_double_room = get_or_create_product('Konaklama — Double Oda (FB)', uom_name=uom_night.name)
    p_single_room = get_or_create_product('Konaklama — Single Oda (FB)', uom_name=uom_night.name)
    p_vip_suite = get_or_create_product('Konaklama — VIP Suite Oda (FB)', uom_name=uom_night.name)
    p_transfer_std = get_or_create_product('Transfer — Standart Araç (Havalimanı ↔ Otel)', uom_name=uom_person.name)
    p_transfer_vip = get_or_create_product('Transfer — VIP Araç (Havalimanı ↔ Otel)', uom_name=uom_person.name)
    p_meeting_room = get_or_create_product('Toplantı Salonu Kirası', uom_name=uom_day.name)
    p_tech_equip = get_or_create_product('Teknik Ekipman (Projeksiyon & Ses Sistemi)', uom_name=uom_day.name)
    p_gala = get_or_create_product('Gala Akşam Yemeği', uom_name=uom_person.name)
    p_flight_go = get_or_create_product('Uçuş — Gidiş (İstanbul → Destinasyon)', uom_name=uom_person.name)
    p_flight_ret = get_or_create_product('Uçuş — Dönüş (Destinasyon → İstanbul)', uom_name=uom_person.name)

    # ---- Partner/Otel ----
    print('Otel partnerleri oluşturuluyor...')
    hotel_kaya = get_or_create_partner('Kaya Palazzo Golf & Resort ★★★★★')
    hotel_maxx = get_or_create_partner('Maxx Royal Belek Golf Resort ★★★★★')
    hotel_merit = get_or_create_partner('Merit Crystal Cove Hotel ★★★★★')
    hotel_elexus = get_or_create_partner('Elexus Hotel & Resort & Spa ★★★★★')

    # ---- Lokasyonlar ----
    loc_antalya = get_state(['Antalya'], country_code='TR')
    loc_kibris = get_state(['Kıbrıs', 'Lefkoşa', 'Cyprus', 'Northern Cyprus'])
    if not loc_kibris:
        loc_kibris = get_state(['Nicosia', 'Lefkosa'])

    print(f'Lokasyonlar: Antalya={loc_antalya and loc_antalya.name}, Kıbrıs={loc_kibris and loc_kibris.name}')

    # ---- İHALE ----
    print('\nİhale oluşturuluyor...')

    # Mevcut MICE ihaleleri kontrol et
    existing = env['ak.tender'].search([
        ('name', '=', '2026 Yılsonu Toplantısı — MICE İhalesi')
    ], limit=1)

    if existing:
        print(f'  UYARI: Bu isimde ihale zaten mevcut (ID: {existing.id}). Yeni ihale oluşturuluyor...')

    # En temel zorunlu alanlarla oluştur (workflow gereksinimlerine göre ayarla)
    from datetime import datetime, timedelta
    now = datetime.now()
    tender_vals = {
        'name': '2026 Yılsonu Toplantısı — MICE İhalesi',
        'tender_type': 'mice',
        'currency_id': try_currency.id,
        'total_person_count': 112,
        'vip_person_count': 2,
        'start_date': now,
        'end_date': now + timedelta(days=30),
    }
    # Opsiyonel alanlar — mevcut alanlar varsa ekle
    try:
        tender_vals['description'] = (
            'Yıllık mümessil toplantısı ve ödül töreni. '
            '100 mümessil, 10 yönetici, 2 tepe yönetici. '
            'Antalya ve Kıbrıs alternatifleri değerlendirilecek.'
        )
    except Exception:
        pass

    tender = env['ak.tender'].create(tender_vals)
    print(f'  İhale oluşturuldu: {tender.name} (ID: {tender.id})')
    env.cr.commit()

    # ============================================================
    # SENARYO OLUŞTURMA YARDIMCISI
    # ============================================================

    def create_scenario(name, scenario_type, parent_id=False, location_id=False,
                        hotel_partner_id=False, meal_plan='fb', person_count=112,
                        vip_count=2, is_mandatory=True):
        """Senaryo oluştur."""
        vals = {
            'tender_id': tender.id,
            'name': name,
            'scenario_type': scenario_type,
            'parent_id': parent_id.id if parent_id else False,
            'location_id': location_id.id if location_id else False,
            'hotel_partner_id': hotel_partner_id.id if hotel_partner_id else False,
            'meal_plan': meal_plan if scenario_type != 'region' else False,
            'person_count': person_count if scenario_type != 'region' else 0,
            'vip_count': vip_count if scenario_type != 'region' else 0,
            'is_mandatory': is_mandatory,
            'scenario_source': 'buyer',
            'scenario_status': 'active',
        }
        return env['ak.tender.scenario'].create(vals)

    def create_date_option(scenario, date_start, date_end, season_type='low',
                           cost_multiplier=1.0, is_preferred=False, notes=''):
        """Tarih seçeneği oluştur."""
        return env['ak.tender.scenario.date'].create({
            'scenario_id': scenario.id,
            'date_start': date_start,
            'date_end': date_end,
            'season_type': season_type,
            'cost_multiplier': cost_multiplier,
            'is_preferred': is_preferred,
            'notes': notes,
        })

    def create_tender_line(scenario, product, name, quantity, days=1,
                           target_price=0.0, line_type='accommodation',
                           uom=None, room_type=None, meal_plan=None,
                           special_requests='', currency=None):
        """İhale kalemi oluştur (ak.tender.line)."""
        vals = {
            'tender_id': tender.id,
            'scenario_id': scenario.id,
            'product_id': product.id,
            'name': name,
            'quantity': float(quantity),
            'days': days,
            'target_price': float(target_price),
            'line_type': line_type,
            'uom_id': (uom or product.uom_id).id,
        }
        if room_type:
            vals['mice_room_type'] = room_type
        if meal_plan:
            vals['mice_meal_plan'] = meal_plan
        if special_requests:
            vals['mice_special_requests'] = special_requests
        if currency:
            vals['currency_id'] = currency.id
        return env['ak.tender.line'].create(vals)

    # ============================================================
    # BÖLGE 1: ANTALYA
    # ============================================================
    print('\nBölge 1: Antalya senaryoları oluşturuluyor...')

    region_antalya = create_scenario(
        name='Antalya',
        scenario_type='region',
        location_id=loc_antalya,
        is_mandatory=False,
    )
    print(f'  Bölge: {region_antalya.name} (ID: {region_antalya.id})')

    # ---- OTEL A: Kaya Palazzo ----
    otel_kaya = create_scenario(
        name='Kaya Palazzo Golf & Resort ★★★★★ — FB — TRY',
        scenario_type='location_hotel',
        parent_id=region_antalya,
        location_id=loc_antalya,
        hotel_partner_id=hotel_kaya,
        meal_plan='fb',
        person_count=112,
        vip_count=2,
        is_mandatory=True,
    )
    print(f'  Otel A: {otel_kaya.name} (ID: {otel_kaya.id})')

    d_kaya_1 = create_date_option(
        otel_kaya,
        date_start=date(2026, 1, 2),
        date_end=date(2026, 1, 5),
        season_type='low',
        cost_multiplier=1.0,
        is_preferred=True,
        notes='Tercih edilen tarih — düşük sezon avantajı',
    )
    d_kaya_2 = create_date_option(
        otel_kaya,
        date_start=date(2026, 1, 9),
        date_end=date(2026, 1, 12),
        season_type='low',
        cost_multiplier=1.05,
        is_preferred=False,
        notes='Alternatif tarih — aynı sezon +%5',
    )

    # Kaya Palazzo Kalemleri (TRY)
    create_tender_line(otel_kaya, p_double_room,
        'Double Oda — Full Board (100 mümessil, 50 oda)',
        quantity=50, days=3, target_price=12_000,
        line_type='accommodation', uom=uom_night,
        room_type='double', meal_plan='fb',
        special_requests='Birbirine yakın odalar, deniz veya yeşil manzara tercih')

    create_tender_line(otel_kaya, p_single_room,
        'Single Oda — Full Board (10 yönetici)',
        quantity=10, days=3, target_price=8_500,
        line_type='accommodation', uom=uom_night,
        room_type='single', meal_plan='fb',
        special_requests='Yönetici katı veya superior oda')

    create_tender_line(otel_kaya, p_vip_suite,
        'VIP Suite Oda — Full Board (2 tepe yönetici)',
        quantity=2, days=3, target_price=25_000,
        line_type='accommodation', uom=uom_night,
        room_type='suite', meal_plan='fb',
        special_requests='Presidential veya Executive Suite, karşılama ikramı, butler hizmet')

    create_tender_line(otel_kaya, p_transfer_std,
        'Transfer — Antalya Havalimanı ↔ Otel (Standart Araç)',
        quantity=110, days=1, target_price=350,
        line_type='transfer', uom=uom_person,
        special_requests='Gidiş + Dönüş, klimalı otobüs/minibüs')

    create_tender_line(otel_kaya, p_transfer_vip,
        'Transfer — Antalya Havalimanı ↔ Otel (VIP Araç)',
        quantity=2, days=1, target_price=2_500,
        line_type='transfer', uom=uom_person,
        special_requests='VIP sedan/SUV, şoför görevlisi, karşılama')

    create_tender_line(otel_kaya, p_meeting_room,
        'Toplantı Salonu — 120 Kişilik (Tiyatro Düzeni)',
        quantity=1, days=4, target_price=15_000,
        line_type='technical', uom=uom_day,
        special_requests='Sabit sahne, kürsü, simultane çeviri kabini, ikram dahil')

    create_tender_line(otel_kaya, p_tech_equip,
        'Teknik Ekipman — Projeksiyon, Ses & Işık Sistemi',
        quantity=1, days=4, target_price=8_000,
        line_type='technical', uom=uom_day,
        special_requests='LED ekran, wireless mikrofon (5 adet), teknik destek personeli')

    create_tender_line(otel_kaya, p_gala,
        'Gala Akşam Yemeği — Açık Büfe (112 Kişi)',
        quantity=112, days=1, target_price=1_200,
        line_type='meal', uom=uom_person,
        special_requests='Akşam 3. gün, canlı müzik, kokteyl saati dahil, dekor')

    create_tender_line(otel_kaya, p_flight_go,
        'Uçuş Gidiş — İstanbul (SAW/IST) → Antalya (AYT)',
        quantity=112, days=1, target_price=1_800,
        line_type='flight', uom=uom_person,
        currency=try_currency,
        special_requests='2 Ocak 2026, ekonomi sınıfı, bagaj dahil. VIP 2 kişi business sınıfı')

    create_tender_line(otel_kaya, p_flight_ret,
        'Uçuş Dönüş — Antalya (AYT) → İstanbul (SAW/IST)',
        quantity=112, days=1, target_price=1_800,
        line_type='flight', uom=uom_person,
        currency=try_currency,
        special_requests='5 Ocak 2026, ekonomi sınıfı, bagaj dahil. VIP 2 kişi business sınıfı')

    print(f'  Kaya Palazzo kalemleri tamamlandı.')

    # ---- OTEL B: Maxx Royal Belek ----
    otel_maxx = create_scenario(
        name='Maxx Royal Belek Golf Resort ★★★★★ — FB — TRY',
        scenario_type='location_hotel',
        parent_id=region_antalya,
        location_id=loc_antalya,
        hotel_partner_id=hotel_maxx,
        meal_plan='fb',
        person_count=112,
        vip_count=2,
        is_mandatory=True,
    )
    print(f'  Otel B: {otel_maxx.name} (ID: {otel_maxx.id})')

    create_date_option(otel_maxx, date(2026, 1, 2), date(2026, 1, 5),
                       season_type='low', cost_multiplier=1.0, is_preferred=True,
                       notes='Tercih edilen tarih')
    create_date_option(otel_maxx, date(2026, 1, 9), date(2026, 1, 12),
                       season_type='low', cost_multiplier=1.05, is_preferred=False,
                       notes='Alternatif tarih')

    # Maxx Royal Kalemleri (TRY — aynı yapı, farklı hedef fiyat)
    create_tender_line(otel_maxx, p_double_room,
        'Double Oda — Full Board (100 mümessil, 50 oda)',
        quantity=50, days=3, target_price=12_000,
        line_type='accommodation', uom=uom_night,
        room_type='double', meal_plan='fb')

    create_tender_line(otel_maxx, p_single_room,
        'Single Oda — Full Board (10 yönetici)',
        quantity=10, days=3, target_price=8_500,
        line_type='accommodation', uom=uom_night,
        room_type='single', meal_plan='fb',
        special_requests='Superior oda, deniz manzarası tercih')

    create_tender_line(otel_maxx, p_vip_suite,
        'VIP Suite Oda — Full Board (2 tepe yönetici)',
        quantity=2, days=3, target_price=28_000,
        line_type='accommodation', uom=uom_night,
        room_type='presidential', meal_plan='fb',
        special_requests='Havuzlu veya Prestige Suite, özel karşılama')

    create_tender_line(otel_maxx, p_transfer_std,
        'Transfer — Antalya Havalimanı ↔ Otel (Standart Araç)',
        quantity=110, days=1, target_price=350,
        line_type='transfer', uom=uom_person)

    create_tender_line(otel_maxx, p_transfer_vip,
        'Transfer — Antalya Havalimanı ↔ Otel (VIP Araç)',
        quantity=2, days=1, target_price=2_500,
        line_type='transfer', uom=uom_person)

    create_tender_line(otel_maxx, p_meeting_room,
        'Toplantı Salonu — 120 Kişilik',
        quantity=1, days=4, target_price=15_000,
        line_type='technical', uom=uom_day)

    create_tender_line(otel_maxx, p_tech_equip,
        'Teknik Ekipman — Projeksiyon, Ses & Işık',
        quantity=1, days=4, target_price=8_000,
        line_type='technical', uom=uom_day)

    create_tender_line(otel_maxx, p_gala,
        'Gala Akşam Yemeği — Açık Büfe (112 Kişi)',
        quantity=112, days=1, target_price=1_200,
        line_type='meal', uom=uom_person)

    create_tender_line(otel_maxx, p_flight_go,
        'Uçuş Gidiş — İstanbul → Antalya (AYT)',
        quantity=112, days=1, target_price=1_800,
        line_type='flight', uom=uom_person, currency=try_currency)

    create_tender_line(otel_maxx, p_flight_ret,
        'Uçuş Dönüş — Antalya (AYT) → İstanbul',
        quantity=112, days=1, target_price=1_800,
        line_type='flight', uom=uom_person, currency=try_currency)

    print(f'  Maxx Royal kalemleri tamamlandı.')
    env.cr.commit()

    # ============================================================
    # BÖLGE 2: KUZEY KIBRIS
    # ============================================================
    print('\nBölge 2: Kuzey Kıbrıs senaryoları oluşturuluyor...')

    region_kibris = create_scenario(
        name='Kuzey Kıbrıs',
        scenario_type='region',
        location_id=loc_kibris,
        is_mandatory=False,
    )
    print(f'  Bölge: {region_kibris.name} (ID: {region_kibris.id})')

    # ---- OTEL C: Merit Crystal Cove ----
    otel_merit = create_scenario(
        name='Merit Crystal Cove Hotel ★★★★★ — FB — EUR',
        scenario_type='location_hotel',
        parent_id=region_kibris,
        location_id=loc_kibris,
        hotel_partner_id=hotel_merit,
        meal_plan='fb',
        person_count=112,
        vip_count=2,
        is_mandatory=True,
    )
    print(f'  Otel C: {otel_merit.name} (ID: {otel_merit.id})')

    create_date_option(otel_merit, date(2026, 1, 2), date(2026, 1, 5),
                       season_type='low', cost_multiplier=1.0, is_preferred=True,
                       notes='Tercih edilen tarih — düşük sezon EUR avantajı')
    create_date_option(otel_merit, date(2026, 1, 9), date(2026, 1, 12),
                       season_type='low', cost_multiplier=1.05,
                       notes='Alternatif tarih — aynı sezon +%5')

    # Merit Kalemleri (EUR — konaklama ve yerel hizmetler)
    create_tender_line(otel_merit, p_double_room,
        'Double Oda — Full Board (100 mümessil, 50 oda)',
        quantity=50, days=3, target_price=280,
        line_type='accommodation', uom=uom_night,
        room_type='double', meal_plan='fb',
        currency=eur_currency,
        special_requests='Deniz manzarası, birbirine yakın odalar')

    create_tender_line(otel_merit, p_single_room,
        'Single Oda — Full Board (10 yönetici)',
        quantity=10, days=3, target_price=220,
        line_type='accommodation', uom=uom_night,
        room_type='single', meal_plan='fb',
        currency=eur_currency,
        special_requests='Executive oda veya üstü')

    create_tender_line(otel_merit, p_vip_suite,
        'VIP Suite Oda — Full Board (2 tepe yönetici)',
        quantity=2, days=3, target_price=750,
        line_type='accommodation', uom=uom_night,
        room_type='suite', meal_plan='fb',
        currency=eur_currency,
        special_requests='Presidential Suite, özel butler, karşılama ikramı')

    create_tender_line(otel_merit, p_transfer_std,
        'Transfer — Ercan/Larnaka Havalimanı ↔ Otel (Standart Araç)',
        quantity=110, days=1, target_price=25,
        line_type='transfer', uom=uom_person,
        currency=eur_currency)

    create_tender_line(otel_merit, p_transfer_vip,
        'Transfer — Havalimanı ↔ Otel (VIP Araç)',
        quantity=2, days=1, target_price=150,
        line_type='transfer', uom=uom_person,
        currency=eur_currency)

    create_tender_line(otel_merit, p_meeting_room,
        'Toplantı Salonu — 120 Kişilik (Tiyatro Düzeni)',
        quantity=1, days=4, target_price=800,
        line_type='technical', uom=uom_day,
        currency=eur_currency)

    create_tender_line(otel_merit, p_tech_equip,
        'Teknik Ekipman — Projeksiyon, Ses & Işık Sistemi',
        quantity=1, days=4, target_price=400,
        line_type='technical', uom=uom_day,
        currency=eur_currency)

    create_tender_line(otel_merit, p_gala,
        'Gala Akşam Yemeği — Açık Büfe (112 Kişi)',
        quantity=112, days=1, target_price=85,
        line_type='meal', uom=uom_person,
        currency=eur_currency,
        special_requests='Akşam 3. gün, deniz kenarı terasa')

    # Kıbrıs Uçuşları TRY (iç hat benzeri — Ercan)
    create_tender_line(otel_merit, p_flight_go,
        'Uçuş Gidiş — İstanbul (SAW/IST) → Ercan (ECN)',
        quantity=112, days=1, target_price=2_800,
        line_type='flight', uom=uom_person,
        currency=try_currency,
        special_requests='2 Ocak 2026, bagaj dahil. VIP 2 kişi business. Ercan aktarmalı veya direkt.')

    create_tender_line(otel_merit, p_flight_ret,
        'Uçuş Dönüş — Ercan (ECN) → İstanbul (SAW/IST)',
        quantity=112, days=1, target_price=2_800,
        line_type='flight', uom=uom_person,
        currency=try_currency,
        special_requests='5 Ocak 2026, bagaj dahil. VIP 2 kişi business.')

    print('  Merit Crystal Cove kalemleri tamamlandı.')

    # ---- OTEL D: Elexus Hotel ----
    otel_elexus = create_scenario(
        name='Elexus Hotel & Resort & Spa ★★★★★ — FB — EUR',
        scenario_type='location_hotel',
        parent_id=region_kibris,
        location_id=loc_kibris,
        hotel_partner_id=hotel_elexus,
        meal_plan='fb',
        person_count=112,
        vip_count=2,
        is_mandatory=True,
    )
    print(f'  Otel D: {otel_elexus.name} (ID: {otel_elexus.id})')

    create_date_option(otel_elexus, date(2026, 1, 2), date(2026, 1, 5),
                       season_type='low', cost_multiplier=1.0, is_preferred=True,
                       notes='Tercih edilen tarih')
    create_date_option(otel_elexus, date(2026, 1, 9), date(2026, 1, 12),
                       season_type='low', cost_multiplier=1.05,
                       notes='Alternatif tarih')

    # Elexus Kalemleri (EUR — aynı yapı, farklı hedef)
    create_tender_line(otel_elexus, p_double_room,
        'Double Oda — Full Board (100 mümessil, 50 oda)',
        quantity=50, days=3, target_price=265,
        line_type='accommodation', uom=uom_night,
        room_type='double', meal_plan='fb',
        currency=eur_currency)

    create_tender_line(otel_elexus, p_single_room,
        'Single Oda — Full Board (10 yönetici)',
        quantity=10, days=3, target_price=210,
        line_type='accommodation', uom=uom_night,
        room_type='single', meal_plan='fb',
        currency=eur_currency)

    create_tender_line(otel_elexus, p_vip_suite,
        'VIP Suite Oda — Full Board (2 tepe yönetici)',
        quantity=2, days=3, target_price=700,
        line_type='accommodation', uom=uom_night,
        room_type='suite', meal_plan='fb',
        currency=eur_currency,
        special_requests='Honeymoon veya Executive Suite')

    create_tender_line(otel_elexus, p_transfer_std,
        'Transfer — Ercan/Larnaka Havalimanı ↔ Otel (Standart Araç)',
        quantity=110, days=1, target_price=25,
        line_type='transfer', uom=uom_person,
        currency=eur_currency)

    create_tender_line(otel_elexus, p_transfer_vip,
        'Transfer — Havalimanı ↔ Otel (VIP Araç)',
        quantity=2, days=1, target_price=150,
        line_type='transfer', uom=uom_person,
        currency=eur_currency)

    create_tender_line(otel_elexus, p_meeting_room,
        'Toplantı Salonu — 120 Kişilik',
        quantity=1, days=4, target_price=750,
        line_type='technical', uom=uom_day,
        currency=eur_currency)

    create_tender_line(otel_elexus, p_tech_equip,
        'Teknik Ekipman — Projeksiyon, Ses & Işık',
        quantity=1, days=4, target_price=380,
        line_type='technical', uom=uom_day,
        currency=eur_currency)

    create_tender_line(otel_elexus, p_gala,
        'Gala Akşam Yemeği — Açık Büfe (112 Kişi)',
        quantity=112, days=1, target_price=80,
        line_type='meal', uom=uom_person,
        currency=eur_currency)

    create_tender_line(otel_elexus, p_flight_go,
        'Uçuş Gidiş — İstanbul (SAW/IST) → Ercan (ECN)',
        quantity=112, days=1, target_price=2_800,
        line_type='flight', uom=uom_person,
        currency=try_currency)

    create_tender_line(otel_elexus, p_flight_ret,
        'Uçuş Dönüş — Ercan (ECN) → İstanbul (SAW/IST)',
        quantity=112, days=1, target_price=2_800,
        line_type='flight', uom=uom_person,
        currency=try_currency)

    print('  Elexus Hotel kalemleri tamamlandı.')
    env.cr.commit()

    # ============================================================
    # ÖZET
    # ============================================================
    print('\n' + '='*60)
    print('VERİ YÜKLEME TAMAMLANDI!')
    print('='*60)
    print(f'\nİhale ID  : {tender.id}')
    print(f'İhale Adı : {tender.name}')
    print(f'\nSenaryolar: {len(tender.scenario_ids)} adet')
    for sc in tender.scenario_ids:
        prefix = '  ' if sc.parent_id else ''
        print(f'{prefix}[{sc.scenario_type}] {sc.name}')
        if sc.line_ids:
            print(f'{prefix}  → {len(sc.line_ids)} kalem, {len(sc.date_option_ids)} tarih seçeneği')
    print('\nOdoo Backend\'de görüntülemek için:')
    print(f'  Satınalma → MICE İhale Yönetimi → MICE İhaleleri')
    print(f'  veya doğrudan: /web#id={tender.id}&model=ak.tender&view_type=form')
    return tender


# ============================================================
# ÇALIŞTR
# ============================================================
tender = create_mice_tender()
