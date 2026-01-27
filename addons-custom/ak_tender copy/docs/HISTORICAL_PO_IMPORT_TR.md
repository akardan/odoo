# Geçmiş Dönem Satınalma Siparişleri İmport Kılavuzu

## Genel Bakış

Bu modül, SAP'den geçmiş dönem satınalma siparişlerini (Purchase Orders) Excel formatında Odoo'ya import etmenizi sağlar. Import edilen veriler, Superset gibi BI araçlarında dönemsel karşılaştırma ve analiz için kullanılabilir.

## Özellikler

- ✅ Excel tabanlı toplu PO import
- ✅ Otomatik tedarikçi ve ürün eşleştirme
- ✅ Geçmiş dönem işaretleme (`is_historical_import`)
- ✅ Batch takibi (`import_batch`)
- ✅ Duplikasyon kontrolü
- ✅ Superset analiz boyutları desteği

## Kurulum ve Erişim

### Menü Konumu
```
Satın Alma > Yapılandırma > Geçmiş Dönem PO İmport
```

### Gerekli Yetkiler
- Tender Manager (ak_tender.group_tender_manager)

## Excel Format Yapısı

### Zorunlu Kolonlar (14)

| Kolon Adı | Açıklama | Örnek |
|-----------|----------|-------|
| **SIPARIS_NO** | SAP Sipariş Numarası | 4500123456 |
| **SIPARIS_TARIHI** | Sipariş Tarihi (YYYY-MM-DD) | 2023-01-15 |
| **TEDARIKCI_KODU** | Tedarikçi SAP Kodu | T001 |
| **TEDARIKCI_ADI** | Tedarikçi Ünvanı | ABC Tedarik A.Ş. |
| **MALZEME_ADI** | Malzeme/Ürün Açıklaması | Buğday Unu |
| **MALZEME_GRUBU** | SAP Malzeme Grubu | 100 |
| **MIKTAR** | Sipariş Miktarı | 1000 |
| **BIRIM** | Ölçü Birimi | KG |
| **BIRIM_FIYAT** | Birim Fiyat | 15.50 |
| **PARA_BIRIMI** | Para Birimi Kodu | TRY |
| **VADE** | Ödeme Vadesi | 30 Gün |
| **SIRKET_KODU** | SAP Şirket Kodu | 2100 |
| **TESIS** | Tesis/Depo Adı | İlko Merkez |
| **SATIN_ALMACI** | Satınalmacı Adı | Ahmet Yılmaz |

### İsteğe Bağlı Kolonlar (6)

#### 🕐 Zaman Boyutu
- **SIPARIS_TARIHI**: Tarih bazlı analizler için (yıl, çeyrek, ay)
- **TESLIMAT_TARIHI**: Teslimat performans analizi için

#### 📊 İhale Tipi Boyutu
- **IHALE_TIPI**: İhale tipi karşılaştırması için
  - `direct` - Direkt
  - `indirect` - Endirekt  
  - `promotion` - Promosyon
  - `mice` - MICE

#### 👤 Satınalmacı Boyutu
- **SATIN_ALMACI**: Kişi bazlı performans analizi
  - Örn: "Ahmet Yılmaz"

#### 📦 Ürün/Hizmet Boyutu
- **MALZEME_KODU**: SAP malzeme kodu
- **MALZEME_ADI**: Malzeme açıklaması
- **MALZEME_GRUBU**: SAP malzeme grubu (kategori analizi için)

#### 💰 Fiyatlama Boyutu
- **BIRIM_FIYAT**: Birim fiyat
- **TOPLAM_TUTAR**: Toplam tutar
- **PARA_BIRIMI**: Para birimi (TRY, USD, EUR)

#### 📅 Vade Boyutu
- **VADE**: Ödeme vadesi (nakit akışı analizi için)
  - Örn: "30 Gün", "60 Gün", "90 Gün"

#### 🏢 Organizasyon Boyutu
- **SIRKET_KODU**: SAP Şirket Kodu
  - 2100: İlko
  - 2000: Merkez
  - 1100: İlkopol
- **TESIS**: Tesis/Depo adı

#### 🤝 Tedarikçi Boyutu
- **TEDARIKCI_KODU**: SAP tedarikçi kodu
- **TEDARIKCI_ADI**: Tedarikçi ünvanı

### Tam Kolon Listesi

```
SIPARIS_NO          - SAP Sipariş Numarası (Zorunlu)
KALEM_NO            - SAP Kalem Numarası
SIPARIS_TARIHI      - Sipariş Tarihi (Zorunlu, YYYY-MM-DD)
TEDARIKCI_KODU      - Tedarikçi SAP Kodu
TEDARIKCI_ADI       - Tedarikçi Ünvanı (Zorunlu)
MALZEME_KODU        - Malzeme SAP Kodu
MALZEME_ADI         - Malzeme Açıklaması (Zorunlu)
MIKTAR              - Sipariş Miktarı (Zorunlu)
BIRIM               - Ölçü Birimi (KG, LT, AD, vb.)
BIRIM_FIYAT         - Birim Fiyat (Zorunlu)
PARA_BIRIMI         - Para Birimi (TRY, USD, EUR)
TOPLAM_TUTAR        - Toplam Tutar
VADE                - Ödeme Vadesi
IHALE_TIPI          - İhale Tipi (direct/indirect/promotion/mice)
SIRKET_KODU         - SAP Şirket Kodu
TESIS               - Tesis/Depo Adı
SATIN_ALMACI        - Satınalmacı Adı
MALZEME_GRUBU       - SAP Malzeme Grubu
TESLIMAT_TARIHI     - Teslimat Tarihi (YYYY-MM-DD)
NOTLAR              - Ek Notlar
```

## Kullanım Adımları

### 1. Excel Şablonunu İndir

1. **Satın Alma > Yapılandırma > Geçmiş Dönem PO İmport** menüsüne git
2. "Excel Şablonu İndir" butonuna tıkla
3. İndirilen `Gecmis_Donem_PO_Import_Sablonu.xlsx` dosyasını aç

### 2. Excel Dosyasını Hazırla

```excel
# Örnek veri yapısı:
SIPARIS_NO  | KALEM_NO | SIPARIS_TARIHI | TEDARIKCI_ADI    | MALZEME_ADI  | MIKTAR | BIRIM_FIYAT | ...
4500123456  | 10       | 2023-01-15     | ABC Tedarik A.Ş. | Buğday Unu   | 1000   | 15.50       | ...
4500123456  | 20       | 2023-01-15     | ABC Tedarik A.Ş. | Şeker        | 500    | 25.00       | ...
4500123457  | 10       | 2023-02-20     | XYZ Ltd. Şti.    | Ayçiçek Yağı | 2000   | 45.75       | ...
```

**Önemli Notlar:**
- Aynı sipariş numarasına sahip satırlar tek bir PO altında birleştirilir
- Tarih formatı: YYYY-MM-DD (örn: 2023-01-15)
- Sayısal değerlerde Türkçe ayraç kullanmayın (15.50 ✓, 15,50 ✗)

### 3. Import İşlemini Başlat

1. Wizard ekranında Excel dosyasını yükle
2. İşlem seçeneklerini belirle:

#### İşlem Seçenekleri

**Yeni Tedarikçi Oluştur**
- ✅ İşaretli: Sistemde olmayan tedarikçiler otomatik oluşturulur
- ❌ İşaretsiz: Tedarikçi bulunamazsa hata verilir

**Yeni Ürün Oluştur**
- ✅ İşaretli: Sistemde olmayan ürünler otomatik oluşturulur
- ❌ İşaretsiz: Ürün bulunamazsa hata verilir

**Duplikaları Atla**
- ✅ İşaretli: Aynı sipariş numarası varsa atlanır (önerilen)
- ❌ İşaretsiz: Mevcut sipariş güncellenir

**Siparişleri Onayla**
- ✅ İşaretli: Import sonrası siparişler otomatik onaylanır
- ❌ İşaretsiz: Siparişler taslak olarak kalır

3. "İmport Et" butonuna tıkla

### 4. Sonuçları Kontrol Et

Import tamamlandığında özet mesaj görüntülenir:
```
İmport Tamamlandı!

Toplam Satır: 150
Oluşturulan PO: 45
Güncellenen PO: 2
Oluşturulan Satır: 150
Atlanan: 3
```

## Veri Eşleştirme Mantığı

### Tedarikçi Eşleştirme
1. **TEDARIKCI_KODU** → `res.partner.ref` ile eşleştir
2. Bulunamazsa **TEDARIKCI_ADI** → `res.partner.name` ile eşleştir
3. Bulunamazsa ve "Yeni Tedarikçi Oluştur" işaretliyse oluştur

### Ürün Eşleştirme
1. **MALZEME_KODU** → `product.product.default_code` ile eşleştir
2. Bulunamazsa **MALZEME_ADI** → `product.product.name` ile eşleştir
3. Bulunamazsa ve "Yeni Ürün Oluştur" işaretliyse oluştur

### Ölçü Birimi Eşleştirme
Yaygın kısaltmalar otomatik eşleştirilir:
- AD, ADET → Units
- KG → kg
- LT, LITRE → L
- M, METRE → m

### Para Birimi Eşleştirme
- TRY, USD, EUR, GBP vb. ISO kodları desteklenir
- Bulunamazsa şirket varsayılan para birimi kullanılır

## Superset Analiz Örnekleri

### 1. Dönemsel Satınalma Trend Analizi

```sql
SELECT 
    DATE_TRUNC('month', date_order) as ay,
    tender_type as ihale_tipi,
    COUNT(DISTINCT id) as siparis_sayisi,
    SUM(amount_total) as toplam_tutar
FROM purchase_order
WHERE is_historical_import = true
GROUP BY ay, ihale_tipi
ORDER BY ay DESC;
```

### 2. Satınalmacı Performans Analizi

```sql
SELECT 
    EXTRACT(YEAR FROM date_order) as yil,
    EXTRACT(QUARTER FROM date_order) as ceyrek,
    -- SAP satınalmacı bilgisi po.notes içinde olabilir veya user_id kullanılabilir
    user_id,
    COUNT(*) as siparis_sayisi,
    SUM(amount_total) as toplam_harcama,
    AVG(amount_total) as ortalama_siparis_tutari
FROM purchase_order
WHERE is_historical_import = true
GROUP BY yil, ceyrek, user_id;
```

### 3. Tedarikçi Karşılaştırma (Vade Analizi)

```sql
SELECT 
    rp.name as tedarikci,
    apt.name as vade,
    COUNT(DISTINCT po.id) as siparis_sayisi,
    SUM(po.amount_total) as toplam_tutar,
    AVG(po.amount_total) as ortalama_tutar
FROM purchase_order po
JOIN res_partner rp ON po.partner_id = rp.id
LEFT JOIN account_payment_term apt ON po.payment_term_id = apt.id
WHERE po.is_historical_import = true
GROUP BY rp.name, apt.name
ORDER BY toplam_tutar DESC;
```

### 4. İhale Tipi Karşılaştırma

```sql
SELECT 
    tender_type,
    COUNT(*) as siparis_sayisi,
    SUM(amount_total) as toplam_tutar,
    AVG(amount_total) as ortalama_tutar,
    MIN(amount_total) as min_tutar,
    MAX(amount_total) as max_tutar
FROM purchase_order
WHERE is_historical_import = true
    AND tender_type IS NOT NULL
GROUP BY tender_type;
```

### 5. Ürün Grubu Fiyat Trend Analizi

```sql
SELECT 
    DATE_TRUNC('month', po.date_order) as ay,
    pt.categ_id,
    pc.name as kategori,
    AVG(pol.price_unit) as ortalama_birim_fiyat,
    SUM(pol.price_subtotal) as toplam_tutar
FROM purchase_order po
JOIN purchase_order_line pol ON po.id = pol.order_id
JOIN product_product pp ON pol.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
JOIN product_category pc ON pt.categ_id = pc.id
WHERE po.is_historical_import = true
GROUP BY ay, pt.categ_id, pc.name
ORDER BY ay DESC, toplam_tutar DESC;
```

## Geçmiş Dönem Verilerini Filtreleme

Import edilen verileri filtrelemek için:

### Odoo Listesi Filtresi
```python
# Domain filtresi
[('is_historical_import', '=', True)]

# Import batch'e göre
[('import_batch', '=', '20231215_143022')]
```

### SQL Sorgusu
```sql
-- Tüm geçmiş dönem siparişleri
SELECT * FROM purchase_order WHERE is_historical_import = true;

-- Belirli bir import batch
SELECT * FROM purchase_order WHERE import_batch = '20231215_143022';

-- Geçmiş dönem hariç (canlı veriler)
SELECT * FROM purchase_order WHERE is_historical_import = false OR is_historical_import IS NULL;
```

## Sık Karşılaşılan Sorunlar ve Çözümler

### 1. "Tedarikçi bulunamadı" Hatası
**Çözüm:** "Yeni Tedarikçi Oluştur" seçeneğini işaretle veya önce tedarikçileri manuel oluştur.

### 2. "Excel dosyası okunamadı" Hatası
**Çözüm:** 
- Excel dosyasının "Geçmiş_PO" sheet'ine sahip olduğundan emin ol
- Dosya formatının .xlsx olduğunu kontrol et

### 3. Tarih Format Hatası
**Çözüm:** Tarihlerin YYYY-MM-DD formatında olduğundan emin ol (örn: 2023-01-15)

### 4. Pandas Kurulum Hatası
**Çözüm:** Sunucuda pandas kurulu değilse:
```bash
pip install pandas openpyxl xlrd
```

### 5. Duplikasyon Uyarısı
**Çözüm:** "Duplikaları Atla" seçeneğini işaretle veya mevcut siparişleri sil/güncelle.

## Best Practices

1. **Test İmport**: İlk olarak küçük bir veri seti (10-20 satır) ile test et
2. **Veri Hazırlığı**: Excel'de verileri temizle ve formatla
3. **Tedarikçi/Ürün Hazırlığı**: Önce master data'yı oluştur
4. **Batch Takibi**: Import batch numarasını not al
5. **Yedekleme**: Import öncesi veritabanı yedeği al
6. **Döküman**: Import kaynak dosyasını arşivle

## Teknik Detaylar

### Yeni Alanlar (purchase.order)
```python
is_historical_import = fields.Boolean(
    string='Geçmiş Dönem',
    help="Bu sipariş SAP'den geçmiş dönem olarak import edildi"
)

import_batch = fields.Char(
    string='İmport Batch',
    help="Import işlem grubu (tarih-saat formatında)"
)
```

### Import Batch Format
```
YYYYMMDD_HHMMSS
Örnek: 20231215_143022
```

## Destek ve İletişim

Sorunlar için:
- Technical Team: Kardan.Digital
- Modül: ak_tender v0.5+

---

**Son Güncelleme:** 2024-12-24
**Versiyon:** 1.0
