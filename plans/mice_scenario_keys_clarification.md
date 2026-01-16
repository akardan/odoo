# MICE Senaryo Anahtarları - Net Tanım

## Senaryo Nedir?

MICE ihalelerinde **senaryo = benzersiz bir teklif paketi kombinasyonu**

## Senaryo Anahtarları

Her farklı kombinasyon = Ayrı bir senaryo

### 1. **Lokasyon** (Zorunlu)
- Ülke + Şehir veya Bölge
- Örnek: Antalya, Kıbrıs, İstanbul

### 2. **Otel** (Zorunlu)
- Hotel partner seçimi
- Örnek: Chamada Prestige, Flexus Hotel

### 3. **Pansiyon Tipi** (Zorunlu)
- RO (Room Only)
- BB (Bed & Breakfast)
- HB (Half Board - Yarım Pansiyon)
- FB (Full Board - Tam Pansiyon)
- AI (All Inclusive)
- UAI (Ultra All Inclusive)

**Önemli:** Aynı otel, farklı pansiyonlar = **Farklı senaryolar**

### 4. **Tarih Seçenekleri** (Alternatifler)
- Her senaryo için 1 veya daha fazla geçerli tarih aralığı
- Örnek: "2-4 Kasım" VEYA "9-11 Kasım" (alternatif tarihler)
- Tedarikçi tarih bazlı farklı fiyat verebilir

### 5. **Özel Öneri/Teklif** (Opsiyonel)
- Acente veya satın alma ekibinin özel notları
- Örnek: "%15 indirim", "Ücretsiz transfer dahil"

## Örnek Senaryo Kombinasyonları

### Senaryo 1
```
Lokasyon: Antalya
Otel: Chamada Prestige 5⭐
Pansiyon: Yarım Pansiyon (HB)
Tarihler: [2-4 Kas] veya [9-11 Kas]
Özel Öneri: -
```

### Senaryo 2  
```
Lokasyon: Antalya
Otel: Chamada Prestige 5⭐
Pansiyon: Tam Pansiyon (FB) ← Farklı pansiyon!
Tarihler: [2-4 Kas] veya [9-11 Kas]
Özel Öneri: "Tam pansiyonda %15 indirim"
```

### Senaryo 3
```
Lokasyon: Antalya
Otel: Flexus Hotel 4⭐ ← Farklı otel!
Pansiyon: Yarım Pansiyon (HB)
Tarihler: [2-4 Kas] veya [9-11 Kas]
Özel Öneri: -
```

### Senaryo 4
```
Lokasyon: Kıbrıs ← Farklı lokasyon!
Otel: Les Ambassadeurs 5⭐
Pansiyon: All Inclusive (AI) ← Farklı pansiyon!
Tarihler: [2-4 Kas] veya [16-18 Kas] veya [23-25 Kas] ← 3 alternatif!
Özel Öneri: -
```

## Tedarikçi Perspektifi

Tedarikçi şu soruları cevaplayacak:

1. **Hangi senaryolara teklif verebilirim?**
   - Senaryo 1 (Chamada HB) → **EVET, 32,000€**
   - Senaryo 2 (Chamada FB) → **EVET, 39,500€**
   - Senaryo 3 (Flexus HB) → **HAYIR** (Bu otelle çalışmıyorum)
   - Senaryo 4 (Kıbrıs AI) → **EVET, 45,000€**

2. **Tarih bazlı farklı fiyat var mı?**
   - Senaryo 1, Tarih 1 (2-4 Kas): 32,000€
   - Senaryo 1, Tarih 2 (9-11 Kas): 34,500€ (daha yüksek sezon)

3. **Paket veya detay?**
   - Paket fiyat: Tüm senaryoya tek fiyat
   - Detaylı: Her satır (Single oda, Gala yemeği, vb.) ayrı ayrı

## Alıcı (Satın Alma) Perspektifi

Karşılaştırma:
```
SENARYO 1: Chamada HB
  Tedarikçi A: 32,000€ (60 gün vade) → NPV: 30,800€ ⭐
  Tedarikçi B: 31,500€ (90 gün vade) → NPV: 29,200€
  Tedarikçi C: Teklif yok

SENARYO 2: Chamada FB  
  Tedarikçi A: 39,500€ (60 gün vade) → NPV: 38,000€
  Tedarikçi B: 41,000€ (30 gün vade) → NPV: 40,600€
  Tedarikçi C: 38,000€ (Peşin) → NPV: 38,000€ ⭐

SENARYO 3: Flexus HB
  Tedarikçi A: Teklif yok
  Tedarikçi B: 28,500€ (60 gün vade) → NPV: 27,450€ ⭐
  Tedarikçi C: 29,000€ (30 gün vade) → NPV: 28,710€

EN AVANTAJLI: Senaryo 3 (Flexus HB) - Tedarikçi B: 27,450€ NPV
```

## Veri Modeli İlişkisi

```
ak.tender (İhale)
  ↓
  ak.tender.scenario (Senaryo 1: Chamada HB)
    ├─ country_id: Türkiye
    ├─ state_id: Antalya
    ├─ hotel_partner_id: Chamada Prestige
    ├─ meal_plan: 'hb' (Yarım Pansiyon) ← ANAHTAR!
    ├─ date_option_ids:
    │    ├─ Tarih 1: 2-4 Kasım 2025
    │    └─ Tarih 2: 9-11 Kasım 2025
    └─ line_ids (Kalemler):
         ├─ Single Room (65 adet × 3 gün)
         ├─ Double Room (1 adet × 3 gün)
         └─ Gala Yemeği (65 kişi)
```

## Özet

**Farklı Pansiyon = Farklı Senaryo**
- Chamada HB → Senaryo 1
- Chamada FB → Senaryo 2 (ayrı senaryo!)

**Farklı Tarih = Aynı Senaryonun Alternatif Opsiyonu**
- 2-4 Kasım → Tarih Opsiyonu 1
- 9-11 Kasım → Tarih Opsiyonu 2
- (Tedarikçi her ikisine de teklif verebilir, farklı fiyatlarla)

Bu yaklaşım **acente mantığıyla uyumlu** çünkü:
- Acente: "Size 2 teklif var: Chamada HB 32K€, Chamada FB 39K€"
- Sistem: "2 ayrı senaryo: Scenario 1 (HB), Scenario 2 (FB)"
