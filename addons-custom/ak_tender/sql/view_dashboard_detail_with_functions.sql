-- ============================================================================
-- VIEW: view_dashboard_detail (FUNCTION-BASED VERSION)
-- ============================================================================
-- Bu versiyon PostgreSQL fonksiyonları kullanarak çok daha temiz ve
-- yönetilebilir bir kod yapısı sunar.
--
-- KURULUM:
-- 1. Önce fonksiyonları oluştur:
--    psql -U odoo -d dbname -f functions_dashboard_helpers.sql
-- 2. Sonra bu view'ı oluştur:
--    psql -U odoo -d dbname -f view_dashboard_detail_with_functions.sql
-- ============================================================================

DROP VIEW IF EXISTS view_dashboard_detail_prep CASCADE;

CREATE VIEW view_dashboard_detail_prep AS
SELECT
    -- ============================================================================
    -- İHALE VE ÜRÜN BİLGİLERİ / TENDER & PRODUCT INFORMATION
    -- ============================================================================
    t.id as ihale_id,
    t.code as ihale_kodu,
    t.name as ihale_adi,
    tl.id as tender_line_id,
    tl.sequence as line_sira,
    pp.id as product_id,
    pp.default_code as product_kodu,
    COALESCE((pt.name::jsonb)->>'tr_TR', (pt.name::jsonb)->>'en_US', pt.name::text) as urun_adi,
    pc.complete_name as urun_kategorisi,
    COALESCE((uom.name::jsonb)->>'tr_TR', (uom.name::jsonb)->>'en_US', uom.name::text) as birim,
    tl.quantity as miktar,
    tl.days as gun_sayisi,
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
    EXTRACT(YEAR FROM t.end_date) as yil,
    EXTRACT(MONTH FROM t.end_date) as ay,
    EXTRACT(WEEK FROM t.end_date) as hafta,
    TO_CHAR(t.end_date, 'YYYY-MM') as yil_ay,
    
    -- ============================================================================
    -- PARA BİRİMİ VE DÖVİZ KURU / CURRENCY & EXCHANGE RATE
    -- ============================================================================
    curr.name as para_birimi,
    curr.symbol as para_birimi_sembol,
    line_curr.name as line_para_birimi,
    line_curr.symbol as line_para_birimi_sembol,
    COALESCE(latest_rate.rate, 1.0) as doviz_kuru_tl,
    TO_CHAR(latest_rate.name, 'YYYY-MM-DD') as kur_tarihi,
    COALESCE(line_latest_rate.rate, 1.0) as line_doviz_kuru_tl,
    TO_CHAR(line_latest_rate.name, 'YYYY-MM-DD') as line_kur_tarihi,
    
    -- ============================================================================
    -- HEDEF FİYAT / TARGET PRICE
    -- ============================================================================
    tl.target_price,
    tl.target_price * COALESCE(line_latest_rate.rate, 1.0) as target_price_tl,
    tl.target_discount,
    (tl.target_price * (1 - tl.target_discount/100) * tl.quantity) as target_total_untaxed,
    (tl.target_price * (1 - tl.target_discount/100) * tl.quantity * COALESCE(line_latest_rate.rate, 1.0)) as target_total_untaxed_tl,
    
    -- ============================================================================
    -- İLK TUR FİYATLAR (Round 1) - FONKSIYON KULLANIMI
    -- ============================================================================
    get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'unit', false) as ilk_tur_birim_fiyat,
    get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'unit', true) as ilk_tur_birim_fiyat_tl,
    get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'total', false) as ilk_tur_toplam_fiyat,
    get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'total', true) as ilk_tur_toplam_fiyat_tl,
    
    -- ============================================================================
    -- MEVCUT TUR FİYATLAR (Current Round) - FONKSIYON KULLANIMI
    -- ============================================================================
    get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'unit', false) as mevcut_tur_birim_fiyat,
    get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'unit', true) as mevcut_tur_birim_fiyat_tl,
    get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'total', false) as mevcut_tur_toplam_fiyat,
    get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'total', true) as mevcut_tur_toplam_fiyat_tl,
    
    -- ============================================================================
    -- SAVING HESAPLAMALARI / SAVINGS CALCULATIONS
    -- ============================================================================
    get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'total', false) - 
    get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'total', false) as saving_tutar,
    
    get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'total', true) - 
    get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'total', true) as saving_tutar_tl,
    
    CASE
        WHEN get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'total', false) > 0 
        THEN ROUND(
            (get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'total', false) - 
             get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'total', false)) / 
            get_round1_min_price(t.id, tl.product_id, pp.product_tmpl_id, 'total', false) * 100, 
            2
        )
        ELSE 0
    END AS saving_yuzdesi,
    
    -- ============================================================================
    -- YAKINLIK ORANI / PROXIMITY RATIO
    -- ============================================================================
    CASE
        WHEN tl.target_price > 0 
        THEN ROUND(
            get_current_round_min_price(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, 'unit', false) / 
            tl.target_price * 100, 
            0
        )
        ELSE 0
    END AS yakinlik_orani_yuzde,
    
    -- ============================================================================
    -- TEDARİKÇİ BİLGİLERİ / SUPPLIER INFORMATION
    -- ============================================================================
    (
        SELECT COUNT(DISTINCT po2.partner_id)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND pol2.price_unit > 0
    ) AS tedarikci_sayisi,
    
    (
        SELECT partner.name
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_partner partner ON po2.partner_id = partner.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
        ORDER BY (pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
        LIMIT 1
    ) AS en_dusuk_teklif_veren,
    
    -- ============================================================================
    -- VADE VE NPV / PAYMENT TERMS & NPV
    -- ============================================================================
    COALESCE((
        SELECT MAX(COALESCE(ptl.nb_days, 0))
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        LEFT JOIN account_payment_term pt2 ON po2.payment_term_id = pt2.id
        LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
    ), 0) AS vade_gun,
    
    -- NPV Kazancı - FONKSIYON KULLANIMI
    get_npv_gain(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, false) as npv_kazanci,
    get_npv_gain(t.id, t.tender_round, tl.product_id, pp.product_tmpl_id, true) as npv_kazanci_tl,
    
    -- ============================================================================
    -- WORKFLOW VE İHALE TİPİ / WORKFLOW & TENDER TYPE
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
    END AS ihale_tipi_label,
    
    -- ============================================================================
    -- DİĞER BİLGİLER / OTHER INFORMATION
    -- ============================================================================
    t.is_urgent as acil_mi,
    country.name as ulke,
    t.city as sehir,
    tl.required_delivery_date as teslimat_tarihi,
    tl.lead_time_days as temin_suresi_gun,
    tl.required as gerekli_mi,
    tl.allow_alternative as alternatif_kabul_mi

FROM ak_tender t
JOIN ak_tender_line tl ON tl.tender_id = t.id 
    AND (tl.display_type = 'product' OR tl.display_type IS NULL)
LEFT JOIN product_product pp ON tl.product_id = pp.id
LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
LEFT JOIN product_category pc ON pt.categ_id = pc.id
LEFT JOIN uom_uom uom ON tl.uom_id = uom.id
LEFT JOIN purchase_requisition_line prl ON tl.id = prl.tender_line_id
LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
LEFT JOIN res_currency curr ON t.currency_id = curr.id
LEFT JOIN res_currency line_curr ON tl.currency_id = line_curr.id
LEFT JOIN res_country country ON t.country_id = country.id

-- Currency Rate Laterals (sadece gösterim için, fonksiyonlar içinde hesaplanıyor)
LEFT JOIN LATERAL (
    SELECT
        CASE
            WHEN curr.name = 'TRY' THEN 1.0
            ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
        END AS rate,
        cr.name
    FROM res_currency_rate cr
    LEFT JOIN LATERAL (
        SELECT cr_t.rate
        FROM res_currency_rate cr_t
        JOIN res_company comp ON comp.id = COALESCE(t.company_id, 1)
        WHERE cr_t.currency_id = comp.currency_id
        AND (cr_t.company_id = t.company_id OR cr_t.company_id IS NULL)
        AND cr_t.name <= CURRENT_DATE
        ORDER BY cr_t.name DESC
        LIMIT 1
    ) cr_try ON true
    WHERE cr.currency_id = t.currency_id
    AND (cr.company_id = t.company_id OR cr.company_id IS NULL)
    AND cr.name <= CURRENT_DATE
    ORDER BY cr.name DESC
    LIMIT 1
) latest_rate ON true

LEFT JOIN LATERAL (
    SELECT
        CASE
            WHEN line_curr.name = 'TRY' THEN 1.0
            ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
        END AS rate,
        cr.name
    FROM res_currency_rate cr
    LEFT JOIN LATERAL (
        SELECT cr_t.rate
        FROM res_currency_rate cr_t
        JOIN res_company comp ON comp.id = COALESCE(t.company_id, 1)
        WHERE cr_t.currency_id = comp.currency_id
        AND (cr_t.company_id = t.company_id OR cr_t.company_id IS NULL)
        AND cr_t.name <= CURRENT_DATE
        ORDER BY cr_t.name DESC
        LIMIT 1
    ) cr_try ON true
    WHERE cr.currency_id = tl.currency_id
    AND (cr.company_id = t.company_id OR cr.company_id IS NULL)
    AND cr.name <= CURRENT_DATE
    ORDER BY cr.name DESC
    LIMIT 1
) line_latest_rate ON true

ORDER BY t.end_date DESC, t.id DESC, tl.sequence;

-- ============================================================================
-- PERFORMANS NOTU
-- ============================================================================
-- Bu view fonksiyon kullandığı için daha temiz ama yine de yavaş olabilir.
-- Production ortamında MATERIALIZED VIEW kullanmanız önerilir:
--
-- Önce normal view'ı oluşturun (yukarıdaki CREATE VIEW komutu)
-- Sonra materialized view oluşturmak için:
--
-- DROP VIEW IF EXISTS view_dashboard_detail CASCADE;
-- DROP MATERIALIZED VIEW IF EXISTS view_dashboard_detail CASCADE;
-- CREATE MATERIALIZED VIEW view_dashboard_detail AS
-- SELECT
--     -- (Yukarıdaki tüm SELECT içeriğini buraya kopyalayın)
-- FROM ak_tender t
-- ...
-- ORDER BY t.end_date DESC, t.id DESC, tl.sequence;
--
-- CREATE UNIQUE INDEX idx_view_dashboard_detail_unique
-- ON view_dashboard_detail (ihale_id, tender_line_id);
--
-- REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
-- ============================================================================
