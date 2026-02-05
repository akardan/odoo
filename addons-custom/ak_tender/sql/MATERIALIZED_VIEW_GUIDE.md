# Materialized View Kullanım Kılavuzu

## Nedir?

**Materialized View**, normal view'dan farklı olarak sonuçları fiziksel olarak saklar. Bu sayede:
- ✅ Sorgu performansı 10-100x daha hızlıdır
- ✅ Karmaşık hesaplamalar sadece bir kez yapılır
- ✅ Index eklenebilir
- ❌ Periyodik olarak refresh edilmesi gerekir
- ❌ Biraz daha fazla disk alanı kullanır

## Kurulum

### 1. Materialized View Oluşturma

```bash
# Normal view'ı materialized view'a çevir
psql -U odoo -d your_database_name -f /opt/odoo18/addons-custom/ak_tender/sql/create_materialized_view_full.sql
```

### 2. Index Ekleme (Performans için önemli!)

```sql
-- Unique index (CONCURRENTLY refresh için gerekli)
CREATE UNIQUE INDEX idx_view_dashboard_detail_unique 
ON view_dashboard_detail (ihale_id, tender_line_id);

-- Sık kullanılan filtreler için indexler
CREATE INDEX idx_view_dashboard_detail_ihale_kodu 
ON view_dashboard_detail (ihale_kodu);

CREATE INDEX idx_view_dashboard_detail_product 
ON view_dashboard_detail (product_id);

CREATE INDEX idx_view_dashboard_detail_dates 
ON view_dashboard_detail (ihale_baslangic, ihale_bitis);

CREATE INDEX idx_view_dashboard_detail_buyer 
ON view_dashboard_detail (buyer_id);

CREATE INDEX idx_view_dashboard_detail_yil_ay 
ON view_dashboard_detail (yil_ay);
```

## Refresh (Güncelleme)

### Manuel Refresh

```sql
-- Basit refresh (view'ı kilitler, hızlıdır)
REFRESH MATERIALIZED VIEW view_dashboard_detail;

-- Concurrent refresh (view'ı kilitlemez, yavaştır ama production için önerilir)
-- NOT: Unique index gerektirir!
REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
```

### Otomatik Refresh (Cron Job)

#### Yöntem 1: PostgreSQL Cron Extension

```sql
-- pg_cron extension'ı yükle (superuser gerektirir)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Her 15 dakikada bir refresh et
SELECT cron.schedule(
    'refresh-dashboard-view',
    '*/15 * * * *',
    'REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail'
);

-- Cron job'ları listele
SELECT * FROM cron.job;

-- Cron job'u sil
SELECT cron.unschedule('refresh-dashboard-view');
```

#### Yöntem 2: Linux Cron

```bash
# Crontab'ı düzenle
crontab -e

# Her 15 dakikada bir refresh et
*/15 * * * * psql -U odoo -d your_database_name -c "REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;" >> /var/log/odoo/dashboard_refresh.log 2>&1

# Her saat başı refresh et
0 * * * * psql -U odoo -d your_database_name -c "REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;" >> /var/log/odoo/dashboard_refresh.log 2>&1

# Her gün 02:00'de refresh et
0 2 * * * psql -U odoo -d your_database_name -c "REFRESH MATERIALIZED VIEW view_dashboard_detail;" >> /var/log/odoo/dashboard_refresh.log 2>&1
```

#### Yöntem 3: Odoo Scheduled Action

Odoo'da Scheduled Action oluşturun:

```python
# Model: ir.cron
# Name: Refresh Dashboard Materialized View
# Interval: 15 minutes
# Code:

env.cr.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail")
env.cr.commit()
```

## Performans Karşılaştırması

### Normal View
```sql
-- İlk sorgu: ~5-30 saniye
SELECT * FROM view_dashboard_detail WHERE ihale_kodu = 'İHALE-2025-0084';
```

### Materialized View (Index ile)
```sql
-- İlk sorgu: ~0.1-0.5 saniye (10-100x daha hızlı!)
SELECT * FROM view_dashboard_detail WHERE ihale_kodu = 'İHALE-2025-0084';
```

## Disk Kullanımı

```sql
-- Materialized view boyutunu kontrol et
SELECT 
    pg_size_pretty(pg_total_relation_size('view_dashboard_detail')) AS total_size,
    pg_size_pretty(pg_relation_size('view_dashboard_detail')) AS table_size,
    pg_size_pretty(pg_indexes_size('view_dashboard_detail')) AS indexes_size;
```

## Refresh Süresi

```sql
-- Refresh süresini ölç
\timing on
REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
\timing off
```

Tipik refresh süreleri:
- 1,000 satır: ~1-2 saniye
- 10,000 satır: ~5-10 saniye
- 100,000 satır: ~30-60 saniye

## Monitoring

### Refresh Durumunu Kontrol Et

```sql
-- Son refresh zamanını kontrol et (custom tablo gerektirir)
CREATE TABLE IF NOT EXISTS materialized_view_refresh_log (
    view_name TEXT,
    refresh_started_at TIMESTAMP,
    refresh_completed_at TIMESTAMP,
    duration INTERVAL,
    row_count BIGINT,
    status TEXT
);

-- Refresh script'i (log ile)
DO $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    row_cnt BIGINT;
BEGIN
    start_time := clock_timestamp();
    
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
    
    end_time := clock_timestamp();
    
    SELECT COUNT(*) INTO row_cnt FROM view_dashboard_detail;
    
    INSERT INTO materialized_view_refresh_log 
    VALUES (
        'view_dashboard_detail',
        start_time,
        end_time,
        end_time - start_time,
        row_cnt,
        'SUCCESS'
    );
END $$;

-- Log'ları görüntüle
SELECT * FROM materialized_view_refresh_log 
ORDER BY refresh_completed_at DESC 
LIMIT 10;
```

## Troubleshooting

### Problem 1: CONCURRENTLY refresh çalışmıyor

**Hata**: `ERROR: cannot refresh materialized view "view_dashboard_detail" concurrently`

**Çözüm**: Unique index eklemelisiniz
```sql
CREATE UNIQUE INDEX idx_view_dashboard_detail_unique 
ON view_dashboard_detail (ihale_id, tender_line_id);
```

### Problem 2: Refresh çok yavaş

**Çözümler**:
1. CONCURRENTLY yerine normal refresh kullanın (off-peak saatlerde)
2. Daha az sıklıkta refresh edin
3. Partial refresh yapın (PostgreSQL 13+)

### Problem 3: Disk doldu

**Çözüm**: Eski indexleri temizleyin
```sql
-- Kullanılmayan indexleri bul
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' 
AND tablename = 'view_dashboard_detail'
AND idx_scan = 0;
```

## Normal View'a Geri Dönme

Eğer materialized view'dan vazgeçmek isterseniz:

```sql
-- Materialized view'ı sil
DROP MATERIALIZED VIEW IF EXISTS view_dashboard_detail CASCADE;

-- Normal view'ı yeniden oluştur
\i /opt/odoo18/addons-custom/ak_tender/sql/view_dashboard_detail.sql
```

## Best Practices

1. **Unique Index Ekleyin**: CONCURRENTLY refresh için şart
2. **Sık Kullanılan Kolonlara Index Ekleyin**: Sorgu performansı için
3. **Refresh Sıklığını İyi Ayarlayın**: 
   - Çok sık: Gereksiz yük
   - Çok seyrek: Eski data
   - Önerilen: 15-30 dakika
4. **Off-Peak Saatlerde Full Refresh**: Gece 02:00 gibi
5. **Monitoring Ekleyin**: Refresh sürelerini takip edin
6. **Backup Alın**: Materialized view'ı da backup'a dahil edin

## Alternatif: Incremental Refresh

Eğer sadece değişen satırları güncellemek isterseniz (PostgreSQL 13+):

```sql
-- Trigger ile incremental refresh (gelişmiş)
-- Bu yaklaşım daha karmaşıktır ama çok daha hızlıdır
-- Detaylar için: https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html
```

## Özet

| Özellik | Normal View | Materialized View |
|---------|-------------|-------------------|
| Performans | Yavaş (her sorguda hesaplama) | Çok Hızlı (önceden hesaplanmış) |
| Güncellik | Her zaman güncel | Refresh gerektirir |
| Disk Kullanımı | Minimal | Orta-Yüksek |
| Index | Eklenemez | Eklenebilir |
| Kurulum | Kolay | Orta |
| Bakım | Gereksiz | Refresh scheduling gerekli |
| Önerilen | Küçük datalar, seyrek kullanım | Büyük datalar, sık kullanım |

## Sonuç

Materialized view, dashboard gibi sık kullanılan ve karmaşık hesaplamalar içeren view'lar için idealdir. 15 dakikalık refresh interval ile hem güncel data hem de yüksek performans elde edebilirsiniz.
