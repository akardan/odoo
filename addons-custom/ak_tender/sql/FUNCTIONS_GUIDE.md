# PostgreSQL Fonksiyonları ile View Optimizasyonu

## Neden Fonksiyon Kullanmalıyız?

### Avantajlar ✅
1. **Kod Tekrarını Önler**: Aynı hesaplama 100+ kez yazılmak yerine 1 kez yazılır
2. **Bakım Kolaylığı**: Mantık değiştiğinde sadece fonksiyonu güncellemeniz yeterli
3. **Okunabilirlik**: View çok daha temiz ve anlaşılır olur
4. **Test Edilebilirlik**: Fonksiyonları bağımsız olarak test edebilirsiniz
5. **Yeniden Kullanılabilirlik**: Fonksiyonları başka view'larda da kullanabilirsiniz

### Dezavantajlar ❌
1. **İlk Kurulum**: Fonksiyonları önce oluşturmanız gerekir
2. **Performans**: Çok küçük bir performans kaybı olabilir (genelde ihmal edilebilir)
3. **Debugging**: Hata ayıklama biraz daha karmaşık olabilir

## Oluşturulan Fonksiyonlar

### 1. `is_approved_supplier(partner_id, product_id, product_tmpl_id)`
Tedarikçinin onaylı olup olmadığını kontrol eder.

```sql
SELECT is_approved_supplier(10, 100, 50);
-- Sonuç: true veya false
```

### 2. `get_currency_rate_to_try(currency_id, company_id, date)`
Belirtilen para birimini TL'ye çevirmek için kur hesaplar.

```sql
SELECT get_currency_rate_to_try(2, 1, CURRENT_DATE);
-- Sonuç: 34.5678 (örnek)
```

### 3. `get_round1_min_price(tender_id, product_id, product_tmpl_id, price_type, convert_to_try)`
İlk tur minimum fiyatı hesaplar (onaylı tedarikçi öncelikli).

**Parametreler:**
- `tender_id`: İhale ID
- `product_id`: Ürün ID
- `product_tmpl_id`: Ürün Template ID
- `price_type`: 'unit' (birim fiyat) veya 'total' (toplam fiyat)
- `convert_to_try`: true (TL'ye çevir) veya false (orijinal para birimi)

```sql
-- İlk tur birim fiyat
SELECT get_round1_min_price(1, 100, 50, 'unit', false);

-- İlk tur birim fiyat TL
SELECT get_round1_min_price(1, 100, 50, 'unit', true);

-- İlk tur toplam fiyat
SELECT get_round1_min_price(1, 100, 50, 'total', false);

-- İlk tur toplam fiyat TL
SELECT get_round1_min_price(1, 100, 50, 'total', true);
```

### 4. `get_current_round_min_price(tender_id, tender_round, product_id, product_tmpl_id, price_type, convert_to_try)`
Mevcut tur minimum fiyatı hesaplar (4 seviyeli öncelik).

**Parametreler:**
- `tender_id`: İhale ID
- `tender_round`: Tur numarası
- `product_id`: Ürün ID
- `product_tmpl_id`: Ürün Template ID
- `price_type`: 'unit' (birim fiyat) veya 'total' (toplam fiyat)
- `convert_to_try`: true (TL'ye çevir) veya false (orijinal para birimi)

```sql
-- Mevcut tur birim fiyat
SELECT get_current_round_min_price(1, 2, 100, 50, 'unit', false);

-- Mevcut tur birim fiyat TL
SELECT get_current_round_min_price(1, 2, 100, 50, 'unit', true);

-- Mevcut tur toplam fiyat
SELECT get_current_round_min_price(1, 2, 100, 50, 'total', false);

-- Mevcut tur toplam fiyat TL
SELECT get_current_round_min_price(1, 2, 100, 50, 'total', true);
```

### 5. `get_npv_gain(tender_id, tender_round, product_id, product_tmpl_id, convert_to_try)`
NPV kazancını hesaplar (onaylı tedarikçi öncelikli, 4 seviye).

**Parametreler:**
- `tender_id`: İhale ID
- `tender_round`: Tur numarası
- `product_id`: Ürün ID
- `product_tmpl_id`: Ürün Template ID
- `convert_to_try`: true (TL'ye çevir) veya false (orijinal para birimi)

```sql
-- NPV kazancı
SELECT get_npv_gain(1, 2, 100, 50, false);

-- NPV kazancı TL
SELECT get_npv_gain(1, 2, 100, 50, true);
```

## Kurulum

### Adım 1: Fonksiyonları Oluştur

```bash
psql -U odoo -d your_database_name -f /opt/odoo18/addons-custom/ak_tender/sql/functions_dashboard_helpers.sql
```

### Adım 2: Fonksiyon-Tabanlı View'ı Oluştur

```bash
psql -U odoo -d your_database_name -f /opt/odoo18/addons-custom/ak_tender/sql/view_dashboard_detail_with_functions.sql
```

### Adım 3: (Opsiyonel) Materialized View'a Çevir

```sql
DROP VIEW IF EXISTS view_dashboard_detail CASCADE;

CREATE MATERIALIZED VIEW view_dashboard_detail AS
SELECT * FROM (
    -- view_dashboard_detail_with_functions.sql içeriğini buraya kopyala
) AS subquery;

CREATE UNIQUE INDEX idx_view_dashboard_detail_unique 
ON view_dashboard_detail (ihale_id, tender_line_id);

REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
```

## Karşılaştırma

### Eski Yöntem (Inline Subqueries)
```sql
-- 1000+ satır SQL kodu
-- Her hesaplama için 20-50 satır tekrarlanan kod
-- Bakımı zor
-- Hata ayıklama zor
```

### Yeni Yöntem (Fonksiyonlar)
```sql
-- View sadece 200 satır
-- Her hesaplama tek satır fonksiyon çağrısı
-- Bakımı kolay
-- Fonksiyonları bağımsız test edebilirsiniz
```

## Örnek: View'da Kullanım

### Eski Yöntem
```sql
-- İlk tur birim fiyat (30+ satır)
COALESCE(
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
) as ilk_tur_birim_fiyat
```

### Yeni Yöntem
```sql
-- İlk tur birim fiyat (1 satır!)
get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'unit', false) as ilk_tur_birim_fiyat
```

## Fonksiyon Güncelleme

Eğer mantık değişirse, sadece fonksiyonu güncellemeniz yeterli:

```sql
-- Fonksiyonu güncelle
CREATE OR REPLACE FUNCTION get_round1_min_price(...)
RETURNS NUMERIC AS $$
BEGIN
    -- Yeni mantık buraya
END;
$$ LANGUAGE plpgsql STABLE;

-- View otomatik olarak yeni mantığı kullanır!
-- View'ı yeniden oluşturmanıza gerek yok!
```

## Test Etme

Fonksiyonları bağımsız olarak test edebilirsiniz:

```sql
-- Test 1: Onaylı tedarikçi var mı?
SELECT 
    t.code,
    pp.default_code,
    is_approved_supplier(po.partner_id, pp.id, pp.product_tmpl_id) as is_approved
FROM ak_tender t
JOIN ak_tender_line tl ON tl.tender_id = t.id
JOIN product_product pp ON tl.product_id = pp.id
JOIN purchase_order po ON po.tender_id = t.id
WHERE t.code = 'İHALE-2025-0084'
LIMIT 10;

-- Test 2: İlk tur fiyatları doğru mu?
SELECT 
    t.code,
    pp.default_code,
    get_round1_min_price(t.id, pp.id, pp.product_tmpl_id, 'unit', false) as unit_price,
    get_round1_min_price(t.id, pp.id, pp.product_tmpl_id, 'unit', true) as unit_price_tl,
    get_round1_min_price(t.id, pp.id, pp.product_tmpl_id, 'total', false) as total_price,
    get_round1_min_price(t.id, pp.id, pp.product_tmpl_id, 'total', true) as total_price_tl
FROM ak_tender t
JOIN ak_tender_line tl ON tl.tender_id = t.id
JOIN product_product pp ON tl.product_id = pp.id
WHERE t.code = 'İHALE-2025-0084'
LIMIT 5;

-- Test 3: NPV kazancı doğru mu?
SELECT 
    t.code,
    pp.default_code,
    get_npv_gain(t.id, t.tender_round, pp.id, pp.product_tmpl_id, false) as npv_gain,
    get_npv_gain(t.id, t.tender_round, pp.id, pp.product_tmpl_id, true) as npv_gain_tl
FROM ak_tender t
JOIN ak_tender_line tl ON tl.tender_id = t.id
JOIN product_product pp ON tl.product_id = pp.id
WHERE t.code = 'İHALE-2025-0084'
LIMIT 5;
```

## Performans İpuçları

### 1. STABLE Keyword
Fonksiyonlar `STABLE` olarak işaretlenmiştir. Bu, aynı parametrelerle çağrıldığında sonucun cache'lenebileceği anlamına gelir.

### 2. Materialized View Kullanın
Fonksiyon-tabanlı view'lar yine de yavaş olabilir. Production'da materialized view kullanın:

```bash
# Her 15 dakikada refresh
*/15 * * * * psql -U odoo -d dbname -c "REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;"
```

### 3. Index Ekleyin
Fonksiyonların kullandığı tablolara index ekleyin:

```sql
-- purchase_order indexleri
CREATE INDEX IF NOT EXISTS idx_po_tender_round 
ON purchase_order(tender_id, tender_round, state);

-- purchase_order_line indexleri
CREATE INDEX IF NOT EXISTS idx_pol_product 
ON purchase_order_line(product_id, price_unit);

-- product_supplierinfo indexleri
CREATE INDEX IF NOT EXISTS idx_psi_approved 
ON product_supplierinfo(partner_id, is_approved) 
WHERE is_approved = true;
```

## Troubleshooting

### Problem 1: Fonksiyon bulunamadı

**Hata**: `ERROR: function get_round1_min_price does not exist`

**Çözüm**: Fonksiyonları önce oluşturun
```bash
psql -U odoo -d dbname -f functions_dashboard_helpers.sql
```

### Problem 2: Fonksiyon yavaş çalışıyor

**Çözüm 1**: Indexleri kontrol edin
```sql
-- Eksik indexleri bulun
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('purchase_order', 'purchase_order_line', 'product_supplierinfo');
```

**Çözüm 2**: Materialized view kullanın

### Problem 3: Fonksiyon sonuçları yanlış

**Çözüm**: Fonksiyonu debug edin
```sql
-- Fonksiyon içindeki adımları manuel çalıştırın
SELECT 
    po.id,
    po.partner_id,
    pol.price_unit,
    pol.discount,
    is_approved_supplier(po.partner_id, 100, 50) as is_approved
FROM purchase_order po
JOIN purchase_order_line pol ON pol.order_id = po.id
WHERE po.tender_id = 1
AND pol.product_id = 100
AND po.tender_round = 1
ORDER BY (pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0));
```

## Sonuç

Fonksiyon kullanımı:
- ✅ Kodu %80 daha kısa yapar
- ✅ Bakımı çok daha kolay hale getirir
- ✅ Test edilebilirliği artırır
- ✅ Yeniden kullanılabilirliği sağlar
- ⚠️ İlk kurulum biraz daha karmaşıktır
- ⚠️ Çok küçük performans kaybı olabilir (materialized view ile çözülür)

**Önerilen Yaklaşım**: Fonksiyon-tabanlı view + Materialized view + 15 dakikalık refresh
