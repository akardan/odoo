-- ============================================================================
-- BİRLEŞTİRİLMİŞ DASHBOARD VIEW'LARI
-- Consolidated Dashboard Views for Superset Analytics
-- ============================================================================
-- Tüm view'ları birleştirerek dashboard için optimize edilmiş 2 ana view
-- 2 comprehensive views optimized for dashboard by consolidating all views
-- ============================================================================

-- ============================================================================
-- VIEW 1: GENEL İHALE VE SATINALMACI DASHBOARD (PRIMARY DASHBOARD VIEW)
-- ============================================================================
-- Tüm önemli metrikleri tek bir view'da toplar
-- Combines all key metrics in a single view for main dashboard

DROP VIEW IF EXISTS view_dashboard_main CASCADE;

CREATE VIEW view_dashboard_main AS
SELECT
    -- ============================================================================
    -- TEMEL BİLGİLER / BASIC INFORMATION
    -- ============================================================================
    t.id as ihale_id,
    t.code as ihale_kodu,
    t.name as ihale_adi,
    t.tender_type,
    CASE
        WHEN t.tender_type = 'direct' THEN 'Direkt'
        WHEN t.tender_type = 'indirect' THEN 'Endirekt'
        WHEN t.tender_type = 'mice' THEN 'MICE'
        WHEN t.tender_type = 'promotion' THEN 'Promosyon/Kırtasiye'
        ELSE t.tender_type
    END as ihale_tipi_label,
    
    -- ============================================================================
    -- SATINALMACI BİLGİLERİ / BUYER INFORMATION
    -- ============================================================================
    t.buyer_id,
    COALESCE(buyer_partner.name, 'Atanmamış') as satinalmaci_adi,
    buyer_user.login as satinalmaci_email,
    
    -- ============================================================================
    -- TARİH BİLGİLERİ / DATE INFORMATION
    -- ============================================================================
    t.start_date as ihale_baslangic,
    t.end_date as ihale_bitis,
    t.request_date as talep_tarihi,
    t.required_delivery_date as teslimat_tarihi,
    t.workflow_start_date,
    t.workflow_end_date as tamamlanma_tarihi,
    t.create_date as olusturma_tarihi,
    t.write_date as guncelleme_tarihi,
    
    -- Zaman Analizi / Time Analysis
    EXTRACT(YEAR FROM t.start_date) as yil,
    EXTRACT(MONTH FROM t.start_date) as ay,
    EXTRACT(QUARTER FROM t.start_date) as ceyrek,
    EXTRACT(WEEK FROM t.start_date) as hafta,
    TO_CHAR(t.start_date, 'YYYY-MM') as yil_ay,
    TO_CHAR(t.start_date, 'YYYY-Q') as yil_ceyrek,
    TO_CHAR(t.start_date, 'Mon') as ay_adi,
    TO_CHAR(t.start_date, 'Day') as gun_adi,
    
    -- ============================================================================
    -- WORKFLOW BİLGİLERİ / WORKFLOW INFORMATION
    -- ============================================================================
    t.workflow_current_state_id as workflow_state_id,
    COALESCE((ws.name::jsonb)->>'tr_TR', (ws.name::jsonb)->>'en_US', ws.name::text) as workflow_durumu,
    ws.code as workflow_durum_kodu,
    ws.sequence as workflow_sequence,
    COALESCE((wd.name::jsonb)->>'tr_TR', (wd.name::jsonb)->>'en_US', wd.name::text) as workflow_tanimi,
    
    -- ============================================================================
    -- COĞRAFİ BİLGİLER / GEOGRAPHIC INFORMATION
    -- ============================================================================
    country.name as ulke,
    state.name as il,
    -- t.city as sehir,
    
    -- ============================================================================
    -- PARA BİRİMİ VE DÖVİZ KURU / CURRENCY & EXCHANGE RATE
    -- ============================================================================
    curr.name as para_birimi,
    curr.symbol as para_birimi_sembol,
    COALESCE(1.0 / latest_rate.rate, 1.0) as doviz_kuru_tl,
    TO_CHAR(latest_rate.name, 'YYYY-MM-DD') as kur_tarihi,
    
    -- ============================================================================
    -- FİNANSAL METRIKLER / FINANCIAL METRICS
    -- ============================================================================
    -- Hedef Fiyat Toplamları
    SUM(tl.target_price * tl.quantity) as toplam_hedef_fiyat,
    SUM(tl.target_price * tl.quantity * COALESCE(1.0 / latest_rate.rate, 1.0)) as toplam_hedef_fiyat_tl,
    AVG(tl.target_price) as ortalama_hedef_fiyat,
    AVG(tl.target_price * COALESCE(1.0 / latest_rate.rate, 1.0)) as ortalama_hedef_fiyat_tl,
    
    -- ============================================================================
    -- FİYAT METRIKLERI - ÜRÜN BAZINDA (Her ürün için MIN, sonra topla)
    -- price_subtotal kullanılır, her PO kendi para biriminden TL'ye çevrillir
    -- NOT: Bazı tedarikçiler bazı ürünlere fiyat vermeyebilir, o yüzden ürün bazında hesaplama şart
    -- ============================================================================
    
    -- İlk Tur En Düşük Fiyat (Round 1) - Ürün bazında topla
    SUM(COALESCE((
        SELECT MIN(pol2.price_subtotal)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0)) as ilk_tur_toplam_fiyat,
    SUM(COALESCE((
        SELECT MIN(pol2.price_subtotal * COALESCE((
            SELECT
                CASE
                    WHEN curr2.name = 'TRY' THEN 1.0
                    ELSE COALESCE(1.0 / cr.rate, 1.0)
                END
            FROM res_currency curr2
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = curr2.id
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            WHERE curr2.id = po2.currency_id
        ), 1.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0)) as ilk_tur_toplam_fiyat_tl,
    
    -- Kazanan Tur (Won - Purchase/Done state) - Ürün bazında topla
    SUM(COALESCE((
        SELECT MIN(pol2.price_subtotal)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.state IN ('purchase', 'done')
        AND pol2.price_unit > 0
    ), 0)) as kazanan_toplam_fiyat,
    SUM(COALESCE((
        SELECT MIN(pol2.price_subtotal * COALESCE((
            SELECT
                CASE
                    WHEN curr2.name = 'TRY' THEN 1.0
                    ELSE COALESCE(1.0 / cr.rate, 1.0)
                END
            FROM res_currency curr2
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = curr2.id
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            WHERE curr2.id = po2.currency_id
        ), 1.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.state IN ('purchase', 'done')
        AND pol2.price_unit > 0
    ), 0)) as kazanan_toplam_fiyat_tl,
    
    -- Son Tur En Düşük Fiyat (Current Round) - Ürün bazında topla
    SUM(COALESCE((
        SELECT MIN(pol2.price_subtotal)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0)) as son_tur_toplam_fiyat,
    SUM(COALESCE((
        SELECT MIN(pol2.price_subtotal * COALESCE((
            SELECT
                CASE
                    WHEN curr2.name = 'TRY' THEN 1.0
                    ELSE COALESCE(1.0 / cr.rate, 1.0)
                END
            FROM res_currency curr2
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = curr2.id
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            WHERE curr2.id = po2.currency_id
        ), 1.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0)) as son_tur_toplam_fiyat_tl,
    
    -- Kazanan/Son Tur (Önce kazanan, yoksa son tur - Saving mantığı) - Ürün bazında topla
    SUM(
        COALESCE((
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ), COALESCE((
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ), 0))
    ) as kazanan_son_tur_toplam_fiyat,
    SUM(
        COALESCE((
            SELECT MIN(pol2.price_subtotal * COALESCE((
                SELECT
                    CASE
                        WHEN curr2.name = 'TRY' THEN 1.0
                        ELSE COALESCE(1.0 / cr.rate, 1.0)
                    END
                FROM res_currency curr2
                LEFT JOIN LATERAL (
                    SELECT rate
                    FROM res_currency_rate
                    WHERE currency_id = curr2.id
                    AND name <= CURRENT_DATE
                    ORDER BY name DESC
                    LIMIT 1
                ) cr ON true
                WHERE curr2.id = po2.currency_id
            ), 1.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ), COALESCE((
            SELECT MIN(pol2.price_subtotal * COALESCE((
                SELECT
                    CASE
                        WHEN curr2.name = 'TRY' THEN 1.0
                        ELSE COALESCE(1.0 / cr.rate, 1.0)
                    END
                FROM res_currency curr2
                LEFT JOIN LATERAL (
                    SELECT rate
                    FROM res_currency_rate
                    WHERE currency_id = curr2.id
                    AND name <= CURRENT_DATE
                    ORDER BY name DESC
                    LIMIT 1
                ) cr ON true
                WHERE curr2.id = po2.currency_id
            ), 1.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ), 0))
    ) as kazanan_son_tur_toplam_fiyat_tl,
    
    -- ============================================================================
    -- SAVING METRIKLERI (ÜRÜN BAZINDA)
    -- ============================================================================
    
    -- Toplam Saving (İlk tur - Kazanan/Son tur) - Ürün bazında topla
    SUM(
        COALESCE((
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = 1
            AND pol2.price_unit > 0
        ), 0) -
        COALESCE((
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ), COALESCE((
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ), 0))
    ) as toplam_saving,
    
    SUM(
        COALESCE((
            SELECT MIN(pol2.price_subtotal * COALESCE((
                SELECT
                    CASE
                        WHEN curr2.name = 'TRY' THEN 1.0
                        ELSE COALESCE(1.0 / cr.rate, 1.0)
                    END
                FROM res_currency curr2
                LEFT JOIN LATERAL (
                    SELECT rate
                    FROM res_currency_rate
                    WHERE currency_id = curr2.id
                    AND name <= CURRENT_DATE
                    ORDER BY name DESC
                    LIMIT 1
                ) cr ON true
                WHERE curr2.id = po2.currency_id
            ), 1.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = 1
            AND pol2.price_unit > 0
        ), 0) -
        COALESCE((
            SELECT MIN(pol2.price_subtotal * COALESCE((
                SELECT
                    CASE
                        WHEN curr2.name = 'TRY' THEN 1.0
                        ELSE COALESCE(1.0 / cr.rate, 1.0)
                    END
                FROM res_currency curr2
                LEFT JOIN LATERAL (
                    SELECT rate
                    FROM res_currency_rate
                    WHERE currency_id = curr2.id
                    AND name <= CURRENT_DATE
                    ORDER BY name DESC
                    LIMIT 1
                ) cr ON true
                WHERE curr2.id = po2.currency_id
            ), 1.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ), COALESCE((
            SELECT MIN(pol2.price_subtotal * COALESCE((
                SELECT
                    CASE
                        WHEN curr2.name = 'TRY' THEN 1.0
                        ELSE COALESCE(1.0 / cr.rate, 1.0)
                    END
                FROM res_currency curr2
                LEFT JOIN LATERAL (
                    SELECT rate
                    FROM res_currency_rate
                    WHERE currency_id = curr2.id
                    AND name <= CURRENT_DATE
                    ORDER BY name DESC
                    LIMIT 1
                ) cr ON true
                WHERE curr2.id = po2.currency_id
            ), 1.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ), 0))
    ) as toplam_saving_tl,
    
    -- Saving Yüzdesi (TL bazında)
    CASE
        WHEN SUM(COALESCE((
            SELECT MIN(pol2.price_subtotal * COALESCE((
                SELECT
                    CASE
                        WHEN curr2.name = 'TRY' THEN 1.0
                        ELSE COALESCE(1.0 / cr.rate, 1.0)
                    END
                FROM res_currency curr2
                LEFT JOIN LATERAL (
                    SELECT rate
                    FROM res_currency_rate
                    WHERE currency_id = curr2.id
                    AND name <= CURRENT_DATE
                    ORDER BY name DESC
                    LIMIT 1
                ) cr ON true
                WHERE curr2.id = po2.currency_id
            ), 1.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = 1
            AND pol2.price_unit > 0
        ), 0)) > 0 THEN
            ROUND(((SUM(
                COALESCE((
                    SELECT MIN(pol2.price_subtotal * COALESCE(1.0 / (
                        SELECT rate FROM res_currency_rate
                        WHERE currency_id = po2.currency_id
                        AND name <= CURRENT_DATE
                        ORDER BY name DESC
                        LIMIT 1
                    ), 1.0))
                    FROM purchase_order po2
                    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                    WHERE po2.tender_id = t.id
                    AND pol2.product_id = tl.product_id
                    AND po2.tender_round = 1
                    AND pol2.price_unit > 0
                ), 0) -
                COALESCE((
                    SELECT MIN(pol2.price_subtotal * COALESCE((
                        SELECT
                            CASE
                                WHEN curr2.name = 'TRY' THEN 1.0
                                ELSE COALESCE(1.0 / cr.rate, 1.0)
                            END
                        FROM res_currency curr2
                        LEFT JOIN LATERAL (
                            SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = curr2.id
                            AND name <= CURRENT_DATE
                            ORDER BY name DESC
                            LIMIT 1
                        ) cr ON true
                        WHERE curr2.id = po2.currency_id
                    ), 1.0))
                    FROM purchase_order po2
                    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                    WHERE po2.tender_id = t.id
                    AND pol2.product_id = tl.product_id
                    AND po2.state IN ('purchase', 'done')
                    AND pol2.price_unit > 0
                ), COALESCE((
                    SELECT MIN(pol2.price_subtotal * COALESCE((
                        SELECT
                            CASE
                                WHEN curr2.name = 'TRY' THEN 1.0
                                ELSE COALESCE(1.0 / cr.rate, 1.0)
                            END
                        FROM res_currency curr2
                        LEFT JOIN LATERAL (
                            SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = curr2.id
                            AND name <= CURRENT_DATE
                            ORDER BY name DESC
                            LIMIT 1
                        ) cr ON true
                        WHERE curr2.id = po2.currency_id
                    ), 1.0))
                    FROM purchase_order po2
                    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                    WHERE po2.tender_id = t.id
                    AND pol2.product_id = tl.product_id
                    AND po2.tender_round = t.tender_round
                    AND pol2.price_unit > 0
                ), 0))
            ) / SUM(COALESCE((
                SELECT MIN(pol2.price_subtotal * COALESCE((
                    SELECT
                        CASE
                            WHEN curr2.name = 'TRY' THEN 1.0
                            ELSE COALESCE(1.0 / cr.rate, 1.0)
                        END
                    FROM res_currency curr2
                    LEFT JOIN LATERAL (
                        SELECT rate
                        FROM res_currency_rate
                        WHERE currency_id = curr2.id
                        AND name <= CURRENT_DATE
                        ORDER BY name DESC
                        LIMIT 1
                    ) cr ON true
                    WHERE curr2.id = po2.currency_id
                ), 1.0))
                FROM purchase_order po2
                JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                WHERE po2.tender_id = t.id
                AND pol2.product_id = tl.product_id
                AND po2.tender_round = 1
                AND pol2.price_unit > 0
            ), 0))) * 100)::numeric, 2)
        ELSE 0
    END as saving_yuzdesi,
    
    -- Yakınlık Oranı (Hedef fiyat bazlı - TL)
    CASE
        WHEN SUM(tl.target_price * tl.quantity * COALESCE(1.0 / latest_rate.rate, 1.0)) > 0 THEN
            ROUND(((SUM(
                COALESCE((
                    SELECT MIN(pol2.price_subtotal * COALESCE(1.0 / (
                        SELECT rate FROM res_currency_rate
                        WHERE currency_id = po2.currency_id
                        AND name <= CURRENT_DATE
                        ORDER BY name DESC
                        LIMIT 1
                    ), 1.0))
                    FROM purchase_order po2
                    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                    WHERE po2.tender_id = t.id
                    AND pol2.product_id = tl.product_id
                    AND po2.state IN ('purchase', 'done')
                    AND pol2.price_unit > 0
                ), COALESCE((
                    SELECT MIN(pol2.price_subtotal * COALESCE((
                        SELECT
                            CASE
                                WHEN curr2.name = 'TRY' THEN 1.0
                                ELSE COALESCE(1.0 / cr.rate, 1.0)
                            END
                        FROM res_currency curr2
                        LEFT JOIN LATERAL (
                            SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = curr2.id
                            AND name <= CURRENT_DATE
                            ORDER BY name DESC
                            LIMIT 1
                        ) cr ON true
                        WHERE curr2.id = po2.currency_id
                    ), 1.0))
                    FROM purchase_order po2
                    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                    WHERE po2.tender_id = t.id
                    AND pol2.product_id = tl.product_id
                    AND po2.tender_round = t.tender_round
                    AND pol2.price_unit > 0
                ), 0))
            ) / SUM(tl.target_price * tl.quantity * COALESCE(1.0 / latest_rate.rate, 1.0))) * 100)::numeric, 2)
        ELSE 0
    END as yakinlik_orani_yuzde,
    
    -- ============================================================================
    -- TEDARİKÇİ METRIKLERI / SUPPLIER METRICS
    -- ============================================================================
    (SELECT COUNT(DISTINCT partner_id)
     FROM purchase_order
     WHERE tender_id = t.id) as tedarikci_sayisi,
    (SELECT COUNT(DISTINCT partner_id)
     FROM purchase_order
     WHERE tender_id = t.id AND state IN ('purchase', 'done')) as kazanan_tedarikci_sayisi,
    
    -- Yeni Tedarikçi Sayısı
    (SELECT COUNT(DISTINCT po1.partner_id)
     FROM purchase_order po1
     WHERE po1.tender_id = t.id
     AND po1.state IN ('purchase', 'done')
     AND NOT EXISTS (
         SELECT 1 FROM purchase_order po2
         WHERE po2.partner_id = po1.partner_id
         AND po2.id < po1.id
         AND po2.state IN ('purchase', 'done')
     )) as yeni_tedarikci_sayisi,
    
    -- ============================================================================
    -- ÜRÜN VE MİKTAR BİLGİLERİ / PRODUCT & QUANTITY INFO
    -- ============================================================================
    COUNT(DISTINCT tl.id) as kalem_sayisi,
    SUM(tl.quantity) as toplam_miktar,
    COUNT(DISTINCT tl.product_id) as urun_sayisi,
    
    -- ============================================================================
    -- VADE VE NPV / PAYMENT TERMS & NPV
    -- ============================================================================
    COALESCE(payment_terms.max_days, 0) as maksimum_vade_gun,
    COALESCE(payment_terms.avg_days, 0) as ortalama_vade_gun,
    
    -- NPV Kazancı (PO/POL modellerinden) - Subquery ile
    (SELECT SUM(COALESCE(pol.npv_value, 0))
     FROM purchase_order po
     JOIN purchase_order_line pol ON pol.order_id = po.id
     WHERE po.tender_id = t.id
     AND po.state IN ('purchase', 'done')) as toplam_npv_kazanci,
    (SELECT SUM(COALESCE(pol.npv_value, 0) * COALESCE(1.0 / latest_rate.rate, 1.0))
     FROM purchase_order po
     JOIN purchase_order_line pol ON pol.order_id = po.id
     WHERE po.tender_id = t.id
     AND po.state IN ('purchase', 'done')) as toplam_npv_kazanci_tl,
    
    -- ============================================================================
    -- ZAMAN VE SLA METRIKLERI / TIME & SLA METRICS
    -- ============================================================================
    -- Süre Hesaplamaları (Gün)
    DATE_PART('day', t.end_date - t.start_date)::integer as ihale_suresi_gun,
    
    CASE
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_start_date IS NOT NULL THEN
            DATE_PART('day', t.workflow_end_date - t.workflow_start_date)::integer
        WHEN t.workflow_start_date IS NOT NULL THEN
            DATE_PART('day', NOW() - t.workflow_start_date)::integer
        ELSE NULL
    END as workflow_suresi_gun,
    
    -- Zamanında mı?
    CASE
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_end_date <= t.end_date THEN 'Erken'
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_end_date > t.end_date THEN 'Geç'
        WHEN t.workflow_end_date IS NULL AND NOW() <= t.end_date THEN 'Devam Ediyor'
        WHEN t.workflow_end_date IS NULL AND NOW() > t.end_date THEN 'Geç (Devam Ediyor)'
        ELSE 'Bilinmiyor'
    END as zamaninda_durum,
    
    -- SLA Gecikme (Dakika)
    CASE
        WHEN t.workflow_end_date IS NOT NULL THEN
            DATE_PART('epoch', t.workflow_end_date - t.end_date)::integer / 60
        WHEN t.workflow_end_date IS NULL AND NOW() > t.end_date THEN
            DATE_PART('epoch', NOW() - t.end_date)::integer / 60
        ELSE 0
    END as sla_gecikme_dakika,
    
    -- ============================================================================
    -- WORKFLOW GEÇİŞ İSTATİSTİKLERİ / WORKFLOW TRANSITION STATS
    -- ============================================================================
    (SELECT COUNT(*)
     FROM ak_workflow_transition_history wth2
     WHERE wth2.res_model = 'ak.tender' AND wth2.res_id = t.id) as gecis_sayisi,
    (SELECT COUNT(*)
     FROM ak_workflow_transition_history wth2
     WHERE wth2.res_model = 'ak.tender' AND wth2.res_id = t.id AND wth2.status = 'completed') as tamamlanan_gecis,
    (SELECT COUNT(*)
     FROM ak_workflow_transition_history wth2
     WHERE wth2.res_model = 'ak.tender' AND wth2.res_id = t.id AND wth2.status = 'pending') as bekleyen_gecis,
    (SELECT COUNT(*)
     FROM ak_workflow_transition_history wth2
     WHERE wth2.res_model = 'ak.tender' AND wth2.res_id = t.id AND wth2.status = 'failed') as basarisiz_gecis,
    
    -- Workflow Süre Metrikleri (Saat)
    (SELECT AVG(elapsed_time)
     FROM ak_workflow_transition_history wth2
     WHERE wth2.res_model = 'ak.tender' AND wth2.res_id = t.id) as ortalama_gecis_suresi_saat,
    (SELECT SUM(elapsed_time)
     FROM ak_workflow_transition_history wth2
     WHERE wth2.res_model = 'ak.tender' AND wth2.res_id = t.id) as toplam_gecis_suresi_saat,
    (SELECT MAX(elapsed_time)
     FROM ak_workflow_transition_history wth2
     WHERE wth2.res_model = 'ak.tender' AND wth2.res_id = t.id) as maksimum_gecis_suresi_saat,
    
    -- ============================================================================
    -- DURUM VE ÖZELLIKLER / STATUS & ATTRIBUTES
    -- ============================================================================
    CASE
        WHEN t.end_date < NOW() AND t.workflow_end_date IS NULL THEN 'Süresi Dolmuş'
        WHEN t.start_date > NOW() THEN 'Başlamamış'
        WHEN t.workflow_end_date IS NOT NULL THEN 'Tamamlanmış'
        ELSE 'Aktif'
    END as ihale_durumu,
    
    t.is_urgent as acil_mi,
    t.is_bulk_purchase as toplu_satin_alma_mi,
    t.tender_round as ihale_turu,
    
    -- ============================================================================
    -- OLUŞTURAN VE GÜNCELLEYEN / CREATOR & UPDATER
    -- ============================================================================
    creator.login as olusturan_kullanici,
    updater.login as guncelleyen_kullanici

FROM ak_tender t
    -- Tender Lines (ürün bazında GROUP BY için gerekli)
    INNER JOIN ak_tender_line tl ON tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)
    
    -- Buyer Information
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
    
    -- Workflow Information
    LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
    LEFT JOIN ak_workflow_definition wd ON t.workflow_definition_id = wd.id
    
    -- Geographic Information
    LEFT JOIN res_country country ON t.country_id = country.id
    LEFT JOIN res_country_state state ON t.state_id = state.id
    
    -- Currency
    LEFT JOIN res_currency curr ON t.currency_id = curr.id
    
    -- Latest Exchange Rate (to TRY/TL)
    LEFT JOIN LATERAL (
        SELECT rate, name
        FROM res_currency_rate
        WHERE currency_id = t.currency_id
        AND name <= CURRENT_DATE
        ORDER BY name DESC
        LIMIT 1
    ) latest_rate ON true
    
    -- Payment Terms (maksimum/ortalama vade için)
    LEFT JOIN LATERAL (
        SELECT MAX(COALESCE(ptl.nb_days, 0)) as max_days,
               AVG(COALESCE(ptl.nb_days, 0)) as avg_days
        FROM purchase_order po
        LEFT JOIN account_payment_term pt ON po.payment_term_id = pt.id
        LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt.id
        WHERE po.tender_id = t.id
    ) payment_terms ON true
    
    -- Creator & Updater
    LEFT JOIN res_users creator ON t.create_uid = creator.id
    LEFT JOIN res_users updater ON t.write_uid = updater.id

GROUP BY
    t.id, t.code, t.name, t.tender_type, t.buyer_id,
    t.start_date, t.end_date, t.request_date, t.required_delivery_date,
    t.workflow_start_date, t.workflow_end_date, t.create_date, t.write_date,
    t.workflow_current_state_id, t.workflow_definition_id,
    t.country_id, t.state_id, t.city, t.currency_id,
    t.is_urgent, t.is_bulk_purchase, t.tender_round,
    buyer_partner.name, buyer_user.login,
    ws.name, ws.code, ws.sequence,
    wd.name,
    country.name, state.name,
    curr.name, curr.symbol,
    latest_rate.rate, latest_rate.name,
    payment_terms.max_days, payment_terms.avg_days,
    creator.login, updater.login

ORDER BY t.start_date DESC, t.id DESC;


-- ============================================================================
-- VIEW 2: DETAYLI ÜRÜN VE PERFORMANS ANALİZİ (DETAILED PRODUCT & PERFORMANCE)
-- ============================================================================
-- Ürün bazlı detaylı analizler ve performans metrikleri
-- Product-level detailed analysis and performance metrics

DROP VIEW IF EXISTS view_dashboard_detail CASCADE;

CREATE VIEW view_dashboard_detail AS
SELECT
    -- ============================================================================
    -- ÜRÜN BAZLI BİLGİLER / PRODUCT-LEVEL INFORMATION
    -- ============================================================================
    t.id as ihale_id,
    t.code as ihale_kodu,
    t.name as ihale_adi,
    tl.id as tender_line_id,
    tl.sequence as line_sira,
    
    -- ============================================================================
    -- ÜRÜN DETAYLARI / PRODUCT DETAILS
    -- ============================================================================
    pp.id as product_id,
    pp.default_code as product_kodu,
    COALESCE((pt.name::jsonb)->>'tr_TR', (pt.name::jsonb)->>'en_US', pt.name::text) as urun_adi,
    pc.complete_name as urun_kategorisi,
    COALESCE((uom.name::jsonb)->>'tr_TR', (uom.name::jsonb)->>'en_US', uom.name::text) as birim,
    tl.quantity as miktar,
    tl.days as gun_sayisi,
    
    -- Material Group & Purchasing Group (ERP)
    prl.material_group as malzeme_grubu,
    prl.purchasing_group as satin_alma_grubu,
    
    -- ============================================================================
    -- SATINALMACI VE TARİH / BUYER & DATE
    -- ============================================================================
    t.buyer_id,
    COALESCE(buyer_partner.name, 'Atanmamış') as satinalmaci_adi,
    buyer_user.login as satinalmaci_email,
    
    t.start_date as ihale_baslangic,
    t.end_date as ihale_bitis,
    EXTRACT(YEAR FROM t.start_date) as yil,
    EXTRACT(MONTH FROM t.start_date) as ay,
    TO_CHAR(t.start_date, 'YYYY-MM') as yil_ay,
    
    -- ============================================================================
    -- PARA BİRİMİ VE DÖVİZ KURU / CURRENCY & EXCHANGE RATE
    -- ============================================================================
    curr.name as para_birimi,
    curr.symbol as para_birimi_sembol,
    line_curr.name as line_para_birimi,
    line_curr.symbol as line_para_birimi_sembol,
    COALESCE(1.0 / latest_rate.rate, 1.0) as doviz_kuru_tl,
    TO_CHAR(latest_rate.name, 'YYYY-MM-DD') as kur_tarihi,
    COALESCE(1.0 / line_latest_rate.rate, 1.0) as line_doviz_kuru_tl,
    TO_CHAR(line_latest_rate.name, 'YYYY-MM-DD') as line_kur_tarihi,
    
    -- ============================================================================
    -- ÜRÜN BAZLI FİNANSAL METRIKLER / PRODUCT-LEVEL FINANCIAL METRICS
    -- ============================================================================
    -- Hedef Fiyat
    tl.target_price,
    tl.target_price * COALESCE(1.0 / line_latest_rate.rate, 1.0) as target_price_tl,
    tl.target_discount,
    (tl.target_price * (1 - tl.target_discount) * tl.quantity) as target_total_untaxed,
    (tl.target_price * (1 - tl.target_discount) * tl.quantity * COALESCE(1.0 / line_latest_rate.rate, 1.0)) as target_total_untaxed_tl,
    
    -- İlk Tur En Düşük Fiyat (Bu ürün için)
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) as ilk_tur_birim_fiyat,
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) * COALESCE(1.0 / (
            SELECT rate FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ), 1.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) as ilk_tur_birim_fiyat_tl,
    
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) as ilk_tur_toplam_fiyat,
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) * COALESCE(1.0 / (
            SELECT rate FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ), 1.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) as ilk_tur_toplam_fiyat_tl,
    
    -- Mevcut Tur En Düşük Fiyat (Bu ürün için)
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) as mevcut_tur_birim_fiyat,
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) * COALESCE(1.0 / (
            SELECT rate FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ), 1.0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) as mevcut_tur_birim_fiyat_tl,
    
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) as mevcut_tur_toplam_fiyat,
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) * COALESCE(1.0 / (
            SELECT rate FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ), 1.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) as mevcut_tur_toplam_fiyat_tl,
    
    -- Saving (İlk Tur - Mevcut Tur)
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) - COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) as saving_tutar,
    COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) * COALESCE(1.0 / (
            SELECT rate FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ), 1.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) - COALESCE((
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) * COALESCE(1.0 / (
            SELECT rate FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ), 1.0)) * tl.quantity
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) as saving_tutar_tl,
    
    -- Saving Yüzdesi
    CASE
        WHEN COALESCE((
            SELECT MIN(pol2.price_unit * (1 - pol2.discount)) * tl.quantity
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = 1
            AND pol2.price_unit > 0
        ), 0) > 0 THEN
            ROUND(((COALESCE((
                SELECT MIN(pol2.price_unit * (1 - pol2.discount)) * tl.quantity
                FROM purchase_order po2
                JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                WHERE po2.tender_id = t.id
                AND pol2.product_id = tl.product_id
                AND po2.tender_round = 1
                AND pol2.price_unit > 0
            ), 0) - COALESCE((
                SELECT MIN(pol2.price_unit * (1 - pol2.discount)) * tl.quantity
                FROM purchase_order po2
                JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                WHERE po2.tender_id = t.id
                AND pol2.product_id = tl.product_id
                AND po2.tender_round = t.tender_round
                AND pol2.price_unit > 0
            ), 0)) / COALESCE((
                SELECT MIN(pol2.price_unit * (1 - pol2.discount)) * tl.quantity
                FROM purchase_order po2
                JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                WHERE po2.tender_id = t.id
                AND pol2.product_id = tl.product_id
                AND po2.tender_round = 1
                AND pol2.price_unit > 0
            ), 1) * 100)::numeric, 2)
        ELSE 0
    END as saving_yuzdesi,
    
    -- Yakınlık Oranı (Hedef Fiyata)
    CASE
        WHEN tl.target_price > 0 THEN
            ROUND((COALESCE((
                SELECT MIN(pol2.price_unit * (1 - pol2.discount))
                FROM purchase_order po2
                JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                WHERE po2.tender_id = t.id
                AND pol2.product_id = tl.product_id
                AND po2.tender_round = t.tender_round
                AND pol2.price_unit > 0
            ), 0) / tl.target_price * 100)::numeric, 0)
        ELSE 0
    END as yakinlik_orani_yuzde,
    
    -- ============================================================================
    -- TEDARİKÇİ BİLGİLERİ (ÜRÜN BAZLI) / SUPPLIER INFO (PRODUCT-LEVEL)
    -- ============================================================================
    -- Bu ürün için teklif veren tedarikçi sayısı
    (
        SELECT COUNT(DISTINCT po2.partner_id)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND pol2.price_unit > 0
    ) as tedarikci_sayisi,
    
    -- En düşük teklifi veren tedarikçi
    (
        SELECT partner.name
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_partner partner ON po2.partner_id = partner.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
        ORDER BY pol2.price_unit * (1 - pol2.discount) ASC
        LIMIT 1
    ) as en_dusuk_teklif_veren,
    
    -- ============================================================================
    -- VADE VE NPV (ÜRÜN BAZLI) / PAYMENT TERMS & NPV (PRODUCT-LEVEL)
    -- ============================================================================
    COALESCE((
        SELECT MAX(COALESCE(ptl2.nb_days, 0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        LEFT JOIN account_payment_term pt2 ON po2.payment_term_id = pt2.id
        LEFT JOIN account_payment_term_line ptl2 ON ptl2.payment_id = pt2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) as vade_gun,
    
    COALESCE((
        SELECT pol2.npv_value
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND po2.state IN ('purchase', 'done')
        ORDER BY pol2.price_unit * (1 - pol2.discount) ASC
        LIMIT 1
    ), 0) as npv_kazanci,
    COALESCE((
        SELECT pol2.npv_value * COALESCE(1.0 / (
            SELECT rate FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ), 1.0)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND po2.state IN ('purchase', 'done')
        ORDER BY pol2.price_unit * (1 - pol2.discount) ASC
        LIMIT 1
    ), 0) as npv_kazanci_tl,
    
    -- ============================================================================
    -- WORKFLOW VE DURUM / WORKFLOW & STATUS
    -- ============================================================================
    COALESCE((ws.name::jsonb)->>'tr_TR', ws.name::text) as workflow_durumu,
    ws.code as workflow_durum_kodu,
    
    t.tender_type,
    CASE
        WHEN t.tender_type = 'direct' THEN 'Direkt'
        WHEN t.tender_type = 'indirect' THEN 'Endirekt'
        WHEN t.tender_type = 'mice' THEN 'MICE'
        WHEN t.tender_type = 'promotion' THEN 'Promosyon'
        ELSE t.tender_type
    END as ihale_tipi_label,
    
    -- ============================================================================
    -- DİĞER BİLGİLER / OTHER INFO
    -- ============================================================================
    t.is_urgent as acil_mi,
    country.name as ulke,
    t.city as sehir,
    tl.required_delivery_date as teslimat_tarihi,
    tl.lead_time_days as temin_suresi_gun,
    tl.required as gerekli_mi,
    tl.allow_alternative as alternatif_kabul_mi

FROM ak_tender t
    -- Tender Lines (Her satır bir ürün)
    INNER JOIN ak_tender_line tl ON tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)
    
    -- Product Information
    LEFT JOIN product_product pp ON tl.product_id = pp.id
    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
    LEFT JOIN product_category pc ON pt.categ_id = pc.id
    LEFT JOIN uom_uom uom ON tl.uom_id = uom.id
    
    -- Purchase Requisition Line (ERP Data)
    LEFT JOIN purchase_requisition_line prl ON tl.id = prl.tender_line_id
    
    -- Buyer
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
    
    -- Workflow
    LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
    
    -- Currency & Country
    LEFT JOIN res_currency curr ON t.currency_id = curr.id
    LEFT JOIN res_currency line_curr ON tl.currency_id = line_curr.id
    LEFT JOIN res_country country ON t.country_id = country.id
    
    -- Latest Exchange Rate for Tender Currency (to TRY/TL)
    LEFT JOIN LATERAL (
        SELECT rate, name
        FROM res_currency_rate
        WHERE currency_id = t.currency_id
        AND name <= CURRENT_DATE
        ORDER BY name DESC
        LIMIT 1
    ) latest_rate ON true
    
    -- Latest Exchange Rate for Line Currency (to TRY/TL)
    LEFT JOIN LATERAL (
        SELECT rate, name
        FROM res_currency_rate
        WHERE currency_id = tl.currency_id
        AND name <= CURRENT_DATE
        ORDER BY name DESC
        LIMIT 1
    ) line_latest_rate ON true

ORDER BY t.start_date DESC, t.id DESC, tl.sequence;


-- ============================================================================
-- KULLANIM TALİMATLARI / USAGE INSTRUCTIONS
-- ============================================================================

/*
📊 SUPERSET'TE KULLANIM:

VIEW 1 - view_dashboard_main:
  ✓ Ana KPI kartları (toplam saving, ihale sayısı, ortalamalar)
  ✓ Zaman serisi grafikleri (aylık/çeyreklik trendler)
  ✓ Satınalmacı performans karşılaştırmaları
  ✓ Workflow durum dağılımları
  ✓ Genel özet tablolar

VIEW 2 - view_dashboard_detail:
  ✓ Ürün bazlı detaylı tablolar
  ✓ Kategori analiz grafikleri
  ✓ Tedarikçi performans analizleri
  ✓ Fiyat karşılaştırma tabloları
  ✓ Ürün bazlı saving analizleri

SUPERSET DATASET OLUŞTURMA:
1. Data → Databases → PostgreSQL bağlantınızı seçin
2. Data → Datasets → + Dataset
3. View seçin: view_dashboard_main VEYA view_dashboard_detail
4. Save

CHART OLUŞTURMA ÖRNEKLERİ:
- Bar Chart: satinalmaci_adi vs toplam_saving
- Line Chart: yil_ay vs ortalama_saving_yuzdesi
- Pie Chart: ihale_tipi_label vs ihale sayısı (COUNT)
- Table: Detaylı ihale listesi

FİLTRELEME ÖNERİLERİ:
- yil, ay, yil_ay için zaman filtreleri
- satinalmaci_adi için kullanıcı seçimi
- ihale_tipi_label için tip filtresi
- workflow_durumu için durum filtresi

PERFORMANS İPUCU:
- Büyük veri setleri için date range filtresi kullanın
- Materialized view'a dönüştürmeyi düşünün
- İndeks ekleyin: CREATE INDEX idx_tender_dates ON ak_tender(start_date, end_date);
*/
