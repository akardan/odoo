# View Dashboard Detail - Değişiklik Özeti

## Yapılan Değişiklikler

`view_dashboard_detail.sql` dosyasında **4 alan** güncellendi. Bu alanlar ilk tur fiyat hesaplamalarında **onaylı tedarikçilere öncelik** verecek şekilde değiştirildi.

## Değiştirilen Alanlar

### 1. ilk_tur_birim_fiyat (Satır ~86-116)

**ESKİ KOD:**
```sql
COALESCE((
    SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
    FROM purchase_order po2
    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
    WHERE po2.tender_id = t.id
    AND pol2.product_id = tl.product_id
    AND po2.tender_round = 1
    AND pol2.price_unit > 0
), 0) as ilk_tur_birim_fiyat,
```

**YENİ KOD:**
```sql
-- Önce onaylı tedarikçilerden en düşük fiyatı al, yoksa tüm tekliflerden en düşüğü al
COALESCE(
    -- Onaylı tedarikçilerden en düşük fiyat
    (
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
        AND EXISTS (
            SELECT 1 
            FROM product_supplierinfo psi
            WHERE psi.partner_id = po2.partner_id
            AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
            AND psi.is_approved = true
        )
    ),
    -- Onaylı tedarikçi yoksa tüm tekliflerden en düşük fiyat
    (
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ),
    0
) as ilk_tur_birim_fiyat,
```

### 2. ilk_tur_birim_fiyat_tl (Satır ~118-195)

**ESKİ KOD:**
```sql
COALESCE((
    SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) *
        CASE WHEN po_curr.name = 'TRY' THEN 1.0 
             ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
        END)
    FROM purchase_order po2
    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
    JOIN res_currency po_curr ON po2.currency_id = po_curr.id
    -- ... currency rate joins ...
    WHERE po2.tender_id = t.id
    AND pol2.product_id = tl.product_id
    AND po2.tender_round = 1
    AND pol2.price_unit > 0
), 0) as ilk_tur_birim_fiyat_tl,
```

**YENİ KOD:**
```sql
-- İlk Tur Birim Fiyat TL
-- Önce onaylı tedarikçilerden en düşük fiyatı al, yoksa tüm tekliflerden en düşüğü al
COALESCE(
    -- Onaylı tedarikçilerden en düşük fiyat (TL)
    (
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) *
            CASE WHEN po_curr.name = 'TRY' THEN 1.0 
                 ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
            END)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_currency po_curr ON po2.currency_id = po_curr.id
        -- ... currency rate joins ...
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
        AND EXISTS (
            SELECT 1 
            FROM product_supplierinfo psi
            WHERE psi.partner_id = po2.partner_id
            AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
            AND psi.is_approved = true
        )
    ),
    -- Onaylı tedarikçi yoksa tüm tekliflerden en düşük fiyat (TL)
    (
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) *
            CASE WHEN po_curr.name = 'TRY' THEN 1.0 
                 ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
            END)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_currency po_curr ON po2.currency_id = po_curr.id
        -- ... currency rate joins ...
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ),
    0
) as ilk_tur_birim_fiyat_tl,
```

### 3. ilk_tur_toplam_fiyat (Satır ~197-228)

**ESKİ KOD:**
```sql
COALESCE((
    SELECT MIN(pol2.price_subtotal)
    FROM purchase_order po2
    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
    WHERE po2.tender_id = t.id
    AND pol2.product_id = tl.product_id
    AND po2.tender_round = 1
    AND pol2.price_unit > 0
), 0) as ilk_tur_toplam_fiyat,
```

**YENİ KOD:**
```sql
-- İlk Tur Toplam Fiyat
-- Önce onaylı tedarikçilerden en düşük fiyatı al, yoksa tüm tekliflerden en düşüğü al
COALESCE(
    -- Onaylı tedarikçilerden en düşük toplam fiyat
    (
        SELECT MIN(pol2.price_subtotal)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
        AND EXISTS (
            SELECT 1 
            FROM product_supplierinfo psi
            WHERE psi.partner_id = po2.partner_id
            AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
            AND psi.is_approved = true
        )
    ),
    -- Onaylı tedarikçi yoksa tüm tekliflerden en düşük toplam fiyat
    (
        SELECT MIN(pol2.price_subtotal)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ),
    0
) as ilk_tur_toplam_fiyat,
```

### 4. ilk_tur_toplam_fiyat_tl (Satır ~230-287)

**ESKİ KOD:**
```sql
COALESCE((
    SELECT MIN(pol2.price_subtotal *
        CASE WHEN po_curr.name = 'TRY' THEN 1.0 
             ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
        END)
    FROM purchase_order po2
    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
    JOIN res_currency po_curr ON po2.currency_id = po_curr.id
    -- ... currency rate joins ...
    WHERE po2.tender_id = t.id
    AND pol2.product_id = tl.product_id
    AND po2.tender_round = 1
    AND pol2.price_unit > 0
), 0) as ilk_tur_toplam_fiyat_tl,
```

**YENİ KOD:**
```sql
-- İlk Tur Toplam Fiyat TL
-- Önce onaylı tedarikçilerden en düşük fiyatı al, yoksa tüm tekliflerden en düşüğü al
COALESCE(
    -- Onaylı tedarikçilerden en düşük toplam fiyat (TL)
    (
        SELECT MIN(pol2.price_subtotal *
            CASE WHEN po_curr.name = 'TRY' THEN 1.0 
                 ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
            END)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_currency po_curr ON po2.currency_id = po_curr.id
        -- ... currency rate joins ...
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
        AND EXISTS (
            SELECT 1 
            FROM product_supplierinfo psi
            WHERE psi.partner_id = po2.partner_id
            AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
            AND psi.is_approved = true
        )
    ),
    -- Onaylı tedarikçi yoksa tüm tekliflerden en düşük toplam fiyat (TL)
    (
        SELECT MIN(pol2.price_subtotal *
            CASE WHEN po_curr.name = 'TRY' THEN 1.0 
                 ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
            END)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_currency po_curr ON po2.currency_id = po_curr.id
        -- ... currency rate joins ...
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ),
    0
) as ilk_tur_toplam_fiyat_tl,
```

## Anahtar Değişiklik: EXISTS Kontrolü

Tüm değişikliklerde eklenen kritik kısım:

```sql
AND EXISTS (
    SELECT 1 
    FROM product_supplierinfo psi
    WHERE psi.partner_id = po2.partner_id
    AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
    AND psi.is_approved = true
)
```

Bu kontrol:
- Tedarikçinin (`partner_id`) ürün için kayıtlı olup olmadığını
- Ürün bazında (`product_id`) veya ürün şablonu bazında (`product_tmpl_id`) eşleşme olup olmadığını
- Tedarikçinin onaylı (`is_approved = true`) olup olmadığını kontrol eder

## Etki Analizi

### Doğrudan Etkilenen Alanlar
- `ilk_tur_birim_fiyat`
- `ilk_tur_birim_fiyat_tl`
- `ilk_tur_toplam_fiyat`
- `ilk_tur_toplam_fiyat_tl`

### Dolaylı Etkilenen Alanlar
Bu alanlar yukarıdaki değerleri kullandığı için dolaylı olarak etkilenir:
- `saving_tutar` (ilk_tur_toplam_fiyat - mevcut_tur_toplam_fiyat)
- `saving_tutar_tl` (ilk_tur_toplam_fiyat_tl - mevcut_tur_toplam_fiyat_tl)
- `saving_yuzdesi` (saving hesaplaması)

### Etkilenmeyen Alanlar
- `mevcut_tur_birim_fiyat` - Değişiklik yapılmadı
- `mevcut_tur_birim_fiyat_tl` - Değişiklik yapılmadı
- `mevcut_tur_toplam_fiyat` - Değişiklik yapılmadı
- `mevcut_tur_toplam_fiyat_tl` - Değişiklik yapılmadı
- Diğer tüm alanlar - Değişiklik yapılmadı

## View'ı Güncelleme

View'ı güncellemek için:

```bash
# PostgreSQL'e bağlan
psql -U odoo -d your_database_name

# SQL dosyasını çalıştır
\i /opt/odoo18/addons-custom/ak_tender/sql/view_dashboard_detail.sql
```

veya

```bash
# Tek komutla
psql -U odoo -d your_database_name -f /opt/odoo18/addons-custom/ak_tender/sql/view_dashboard_detail.sql
```

## Gerekli Ön Koşullar

1. `product_supplierinfo` modelinde `is_approved` alanı olmalı (zaten mevcut)
2. `product_supplierinfo` modelinde `partner_type` alanı olmalı (zaten mevcut)
3. Tedarikçiler için `is_approved` değerleri doğru şekilde set edilmiş olmalı

## Test Önerisi

View güncellemesinden sonra aşağıdaki sorguyu çalıştırarak sonuçları kontrol edin:

```sql
SELECT 
    ihale_kodu,
    product_kodu,
    urun_adi,
    ilk_tur_birim_fiyat,
    ilk_tur_toplam_fiyat,
    mevcut_tur_birim_fiyat,
    mevcut_tur_toplam_fiyat,
    saving_tutar,
    saving_yuzdesi
FROM view_dashboard_detail
WHERE ihale_kodu = 'TEST-IHALE-KODU'
ORDER BY product_kodu;
```

## Dosya Bilgileri

- **Dosya**: `addons-custom/ak_tender/sql/view_dashboard_detail.sql`
- **Toplam Satır**: ~1019
- **Değiştirilen Satırlar**: ~86-287 arası (4 alan)
- **Eklenen Satır Sayısı**: ~120 satır (her alan için ~30 satır)
