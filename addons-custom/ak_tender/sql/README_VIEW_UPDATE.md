# View Dashboard Detail - Güncelleme Dökümantasyonu

## Değişiklik Özeti

`view_dashboard_detail` view'ında yapılan değişiklikler, ilk tur fiyat hesaplamalarında **onaylı tedarikçilere öncelik** vermektedir.

## Değiştirilen Alanlar

Aşağıdaki 4 alan güncellendi:

1. **ilk_tur_birim_fiyat** - İlk tur birim fiyat
2. **ilk_tur_birim_fiyat_tl** - İlk tur birim fiyat (TL)
3. **ilk_tur_toplam_fiyat** - İlk tur toplam fiyat
4. **ilk_tur_toplam_fiyat_tl** - İlk tur toplam fiyat (TL)

## Yeni Mantık

### Önceki Davranış
```sql
-- Sadece en düşük fiyatı al (tüm tedarikçilerden)
SELECT MIN(price) FROM purchase_order_line WHERE ...
```

### Yeni Davranış
```sql
-- 1. Önce onaylı tedarikçilerden en düşük fiyatı al
COALESCE(
    (SELECT MIN(price) FROM purchase_order_line 
     WHERE ... AND EXISTS (
         SELECT 1 FROM product_supplierinfo 
         WHERE partner_id = po.partner_id 
         AND is_approved = true
     )),
    -- 2. Onaylı tedarikçi yoksa veya teklif vermediyse, tüm tekliflerden en düşüğü al
    (SELECT MIN(price) FROM purchase_order_line WHERE ...),
    0
)
```

## Onaylı Tedarikçi Kontrolü

Onaylı tedarikçi kontrolü `product_supplierinfo` tablosunda yapılır:

```sql
EXISTS (
    SELECT 1 
    FROM product_supplierinfo psi
    WHERE psi.partner_id = po2.partner_id
    AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
    AND psi.is_approved = true
)
```

### Kontrol Kriterleri:
- Partner ID eşleşmesi
- Ürün ID veya Ürün Template ID eşleşmesi
- `is_approved = true` olması

## View'ı Güncelleme

### Yöntem 1: SQL Dosyasını Çalıştırma
```bash
# PostgreSQL'e bağlan
psql -U odoo -d your_database_name

# SQL dosyasını çalıştır
\i /opt/odoo18/addons-custom/ak_tender/sql/view_dashboard_detail.sql
```

### Yöntem 2: Odoo Üzerinden
```python
# Odoo shell'den
./odoo-bin shell -d your_database_name

# Python kodunu çalıştır
with open('/opt/odoo18/addons-custom/ak_tender/sql/view_dashboard_detail.sql', 'r') as f:
    sql = f.read()
    env.cr.execute(sql)
    env.cr.commit()
```

### Yöntem 3: pgAdmin veya DBeaver
1. SQL dosyasını aç: `addons-custom/ak_tender/sql/view_dashboard_detail.sql`
2. Tüm içeriği kopyala
3. pgAdmin/DBeaver'da Query Tool'u aç
4. SQL'i yapıştır ve çalıştır

## Etkilenen Hesaplamalar

Bu değişiklik aşağıdaki hesaplamaları da etkiler:

- **saving_tutar**: İlk tur ve mevcut tur arasındaki fark (onaylı tedarikçi öncelikli)
- **saving_tutar_tl**: Saving tutarı TL cinsinden (onaylı tedarikçi öncelikli)
- **saving_yuzdesi**: Saving yüzdesi (onaylı tedarikçi öncelikli)

## Test Senaryoları

### Senaryo 1: Onaylı Tedarikçi Var ve Teklif Vermiş
- **Durum**: Ürün için onaylı tedarikçi var ve ilk turda teklif vermiş
- **Beklenen**: Onaylı tedarikçilerin en düşük fiyatı alınır
- **Örnek**: 
  - Onaylı Tedarikçi A: 100 TL
  - Onaylı Tedarikçi B: 120 TL
  - Onaysız Tedarikçi C: 80 TL
  - **Sonuç**: 100 TL (Onaylı tedarikçilerden en düşük)

### Senaryo 2: Onaylı Tedarikçi Yok veya Teklif Vermemiş
- **Durum**: Ürün için onaylı tedarikçi yok veya teklif vermemiş
- **Beklenen**: Tüm tekliflerden en düşük fiyat alınır
- **Örnek**:
  - Onaysız Tedarikçi A: 100 TL
  - Onaysız Tedarikçi B: 120 TL
  - Onaysız Tedarikçi C: 80 TL
  - **Sonuç**: 80 TL (Tüm tekliflerden en düşük)

### Senaryo 3: Hiç Teklif Yok
- **Durum**: İlk turda hiç teklif verilmemiş
- **Beklenen**: 0 değeri döner
- **Sonuç**: 0

## Performans Notları

- Her ürün için 2 subquery çalışır (önce onaylı, sonra tüm tedarikçiler)
- `EXISTS` kullanımı performans için optimize edilmiştir
- `product_supplierinfo` tablosunda `partner_id`, `product_id`, `product_tmpl_id` ve `is_approved` alanlarında index olması önerilir

## Index Önerileri

```sql
-- Performans için önerilen indexler
CREATE INDEX IF NOT EXISTS idx_product_supplierinfo_approved 
ON product_supplierinfo(partner_id, is_approved) 
WHERE is_approved = true;

CREATE INDEX IF NOT EXISTS idx_product_supplierinfo_product 
ON product_supplierinfo(product_id, is_approved) 
WHERE is_approved = true;

CREATE INDEX IF NOT EXISTS idx_product_supplierinfo_template 
ON product_supplierinfo(product_tmpl_id, is_approved) 
WHERE is_approved = true;
```

## Rollback (Geri Alma)

Eğer eski haline dönmek isterseniz, git history'den eski versiyonu alabilirsiniz:

```bash
git log --oneline addons-custom/ak_tender/sql/view_dashboard_detail.sql
git show <commit_hash>:addons-custom/ak_tender/sql/view_dashboard_detail.sql > old_view.sql
psql -U odoo -d your_database_name -f old_view.sql
```

## Değişiklik Tarihi

- **Tarih**: 2026-02-02
- **Geliştirici**: Roo AI Assistant
- **Ticket/Issue**: Onaylı tedarikçi önceliklendirmesi
- **Etkilenen Dosyalar**:
  - `addons-custom/ak_tender/sql/view_dashboard_detail.sql`
  - `addons-custom/ak_tender/models/product_supplier_extension.py` (is_approved field)

## İlgili Modeller

- **ak_tender**: İhale modeli
- **ak_tender_line**: İhale satırı modeli
- **purchase_order**: Satınalma siparişi
- **purchase_order_line**: Satınalma sipariş satırı
- **product_supplierinfo**: Tedarikçi bilgisi (is_approved field ile extend edilmiş)
- **product_product**: Ürün
- **product_template**: Ürün şablonu
