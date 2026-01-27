# Geçmiş Dönem Satınalma Siparişleri İmport - Hızlı Başlangıç

## 📋 Özet

SAP'den geçmiş dönem satınalma siparişlerini Excel formatında Odoo'ya import ederek, Superset'te dönemsel karşılaştırma ve analiz yapmanızı sağlar.

## ⚡ Hızlı Başlangıç

### 1. Menüye Eriş
```
Satın Alma > Yapılandırma > Geçmiş Dönem PO İmport
```

### 2. Excel Şablonunu İndir
- "Excel Şablonu İndir" butonuna tıkla
- Şablon dosyası otomatik indirilir

### 3. Excel Dosyasını Doldur

**Zorunlu Kolonlar (14):**
```
SIPARIS_NO       - SAP Sipariş Numarası
SIPARIS_TARIHI   - Sipariş Tarihi (YYYY-MM-DD)
TEDARIKCI_KODU   - Tedarikçi SAP Kodu
TEDARIKCI_ADI    - Tedarikçi Ünvanı
MALZEME_ADI      - Malzeme/Ürün Adı
MALZEME_GRUBU    - SAP Malzeme Grubu
MIKTAR           - Sipariş Miktarı
BIRIM            - Ölçü Birimi (KG, LT, AD vb.)
BIRIM_FIYAT      - Birim Fiyat
PARA_BIRIMI      - Para Birimi (TRY, USD, EUR)
VADE             - Ödeme Vadesi (30 Gün, 60 Gün)
SIRKET_KODU      - SAP Şirket Kodu (2100, 2000, 1100)
TESIS            - Tesis/Depo Adı
SATIN_ALMACI     - Satınalmacı Adı
```

**İsteğe Bağlı Kolonlar (6):**
```
KALEM_NO         - SAP Kalem Numarası
MALZEME_KODU     - Malzeme SAP Kodu
TOPLAM_TUTAR     - Toplam Tutar
IHALE_TIPI       - İhale tipi (direct/indirect/promotion/mice)
TESLIMAT_TARIHI  - Teslimat Tarihi
NOTLAR           - Ek Notlar
```

### 4. İmport Et
- Excel dosyasını yükle
- "Yeni Tedarikçi Oluştur" ve "Duplikaları Atla" seçeneklerini işaretle
- "İmport Et" butonuna tıkla

## 📊 Analiz Boyutları

Import edilen veriler aşağıdaki boyutlarda analiz edilebilir:

| Boyut | Alan | Kullanım |
|-------|------|----------|
| **Zaman** | SIPARIS_TARIHI | Yıl, çeyrek, ay bazında trend analizi |
| **İhale Tipi** | IHALE_TIPI | Direkt/Endirekt/Promosyon karşılaştırması |
| **Satınalmacı** | SATIN_ALMACI | Kişi bazlı performans analizi |
| **Ürün/Hizmet** | MALZEME_ADI, MALZEME_GRUBU | Kategori bazlı analiz |
| **Fiyatlama** | BIRIM_FIYAT, TOPLAM_TUTAR | Fiyat trend analizi |
| **Vade** | VADE | Nakit akışı analizi |
| **Tedarikçi** | TEDARIKCI_ADI | Tedarikçi performans analizi |
| **Organizasyon** | SIRKET_KODU, TESIS | Lokasyon bazlı analiz |

## 🔍 Verileri Filtreleme

### Odoo'da
```python
# Sadece geçmiş dönem siparişleri
[('is_historical_import', '=', True)]

# Belirli bir import batch
[('import_batch', '=', '20231215_143022')]
```

### Superset/SQL'de
```sql
-- Geçmiş dönem siparişleri
SELECT * FROM purchase_order WHERE is_historical_import = true;

-- Canlı sistem siparişleri (geçmiş dönem hariç)
SELECT * FROM purchase_order 
WHERE is_historical_import = false OR is_historical_import IS NULL;
```

## 📈 Örnek Superset Analizi

### Aylık Satınalma Trendi
```sql
SELECT 
    DATE_TRUNC('month', date_order) as ay,
    tender_type as ihale_tipi,
    COUNT(*) as siparis_sayisi,
    SUM(amount_total) as toplam_tutar
FROM purchase_order
WHERE is_historical_import = true
GROUP BY ay, ihale_tipi
ORDER BY ay DESC;
```

### İhale Tipi Karşılaştırması
```sql
SELECT 
    tender_type,
    COUNT(*) as siparis_sayisi,
    SUM(amount_total) as toplam_tutar,
    AVG(amount_total) as ortalama_tutar
FROM purchase_order
WHERE is_historical_import = true
GROUP BY tender_type;
```

## 📁 Dosyalar

### Kod
- [`models/purchase_order.py`](models/purchase_order.py) - PO model alanları
- [`wizards/import_historical_po_wizard.py`](wizards/import_historical_po_wizard.py) - Import mantığı
- [`wizards/import_historical_po_wizard_views.xml`](wizards/import_historical_po_wizard_views.xml) - UI

### Dokümantasyon
- [`docs/HISTORICAL_PO_IMPORT_TR.md`](docs/HISTORICAL_PO_IMPORT_TR.md) - Detaylı kullanım kılavuzu

## ⚙️ Özellikler

- ✅ Excel template otomatik oluşturma
- ✅ Otomatik tedarikçi/ürün eşleştirme ve oluşturma
- ✅ Duplikasyon kontrolü
- ✅ Batch takibi
- ✅ Hata raporlama
- ✅ Toplu sipariş onaylama
- ✅ Para birimi ve ölçü birimi otomatik eşleştirme

## 🔒 Gereksinimler

- **Python Kütüphaneleri:** pandas, openpyxl
- **Odoo Modül:** ak_tender v0.5+
- **Yetki:** Tender Manager

## 📚 Detaylı Dokümantasyon

Tüm detaylar için: [`docs/HISTORICAL_PO_IMPORT_TR.md`](docs/HISTORICAL_PO_IMPORT_TR.md)

---

**Geliştirici:** Kardan.Digital  
**Versiyon:** 1.0  
**Tarih:** 2024-12-24
