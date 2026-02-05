-- ============================================================================
-- MATERIALIZED VIEW: view_dashboard_detail
-- ============================================================================
-- Bu materialized view, view_dashboard_detail_prep view'ından oluşturulur.
-- Normal view'dan çok daha hızlıdır çünkü sonuçları fiziksel olarak saklar.
-- Ancak periyodik olarak refresh edilmesi gerekir.
--
-- ÖNEMLİ: Bu scripti çalıştırmadan önce şunları yapın:
-- 1. functions_dashboard_helpers.sql dosyasını çalıştırın (fonksiyonları oluşturur)
-- 2. view_dashboard_detail_with_functions.sql dosyasını çalıştırın (prep view'ı oluşturur)
-- 3. Bu dosyayı çalıştırın (materialized view oluşturur)
--
-- KULLANIM:
-- 1. İlk oluşturma: Bu dosyayı çalıştırın
-- 2. Güncelleme: REFRESH MATERIALIZED VIEW view_dashboard_detail;
-- 3. Concurrent refresh (kilitleme olmadan): 
--    REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
--
-- OTOMATİK REFRESH için cron job ekleyin:
-- */15 * * * * psql -U odoo -d dbname -c "REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;"
-- ============================================================================

-- Materialized view varsa sil
DROP MATERIALIZED VIEW IF EXISTS view_dashboard_detail CASCADE;

-- view_dashboard_detail_prep view'ından materialized view oluştur
CREATE MATERIALIZED VIEW view_dashboard_detail AS
SELECT * FROM view_dashboard_detail_prep;

-- Performans için unique index oluştur (concurrent refresh için gerekli)
CREATE UNIQUE INDEX idx_view_dashboard_detail_unique 
ON view_dashboard_detail (ihale_id, tender_line_id);

-- Diğer sık kullanılan sorgular için indexler
CREATE INDEX idx_view_dashboard_detail_ihale_id 
ON view_dashboard_detail (ihale_id);

CREATE INDEX idx_view_dashboard_detail_product_id 
ON view_dashboard_detail (product_id);

CREATE INDEX idx_view_dashboard_detail_buyer_id 
ON view_dashboard_detail (buyer_id);

CREATE INDEX idx_view_dashboard_detail_end_date 
ON view_dashboard_detail (ihale_bitis);

CREATE INDEX idx_view_dashboard_detail_workflow 
ON view_dashboard_detail (workflow_durum_kodu);

-- ============================================================================
-- REFRESH KOMUTU
-- ============================================================================
-- Manuel refresh:
-- REFRESH MATERIALIZED VIEW view_dashboard_detail;
--
-- Concurrent refresh (kilitleme olmadan, daha yavaş ama production için önerilir):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
-- ============================================================================
