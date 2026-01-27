-- ============================================================================
-- VIEW 2: DETAYLI ÜRÜN BAZLI DASHBOARD
-- ============================================================================
-- Her ihale satırı (ürün) için detaylı metrikler
-- Detailed metrics for each tender line (product)
-- 
-- DÖVİZ KURU HESAPLAMA NOTU:
-- Odoo'nun company_rate formülü kullanılıyor: try_rate / foreign_currency_rate
-- Bu formül ak_currency_rate_tcmb modülü tarafından set edilen kurlarla uyumludur.
/*
SELECT * 
FROM view_dashboard_detail
WHERE ihale_kodu ='İHALE-2025-0084'
*/

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
    EXTRACT(YEAR FROM t.end_date) as yil,
    EXTRACT(MONTH FROM t.end_date) as ay,
    EXTRACT(WEEK FROM t.end_date) as hafta,
    TO_CHAR(t.end_date, 'YYYY-MM') as yil_ay,
    
    -- ============================================================================
    -- PARA BİRİMİ VE DÖVİZ KURU / CURRENCY & EXCHANGE RATE
    -- Odoo's company_rate formula: try_rate / foreign_currency_rate
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
    -- ÜRÜN BAZLI FİNANSAL METRIKLER / PRODUCT-LEVEL FINANCIAL METRICS
    -- ============================================================================
    -- Hedef Fiyat
    tl.target_price,
    tl.target_price * COALESCE(line_latest_rate.rate, 1.0) as target_price_tl,
    tl.target_discount,
    (tl.target_price * (1 - tl.target_discount/100) * tl.quantity) as target_total_untaxed,
    (tl.target_price * (1 - tl.target_discount/100) * tl.quantity * COALESCE(line_latest_rate.rate, 1.0)) as target_total_untaxed_tl,
    
    -- ============================================================================
    -- İLK TUR FİYATLAR (Round 1)
    -- ============================================================================
    
    -- İlk Tur Birim Fiyat
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
        SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) *
            CASE WHEN po_curr.name = 'TRY' THEN 1.0 
                 ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
            END)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_currency po_curr ON po2.currency_id = po_curr.id
        LEFT JOIN LATERAL (
            SELECT rate
            FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND (company_id = po2.company_id OR company_id IS NULL)
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ) cr ON true
        LEFT JOIN LATERAL (
            SELECT rate
            FROM res_currency_rate cr_t
            JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
            WHERE cr_t.currency_id = comp.currency_id
            AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
            AND cr_t.name <= CURRENT_DATE
            ORDER BY cr_t.name DESC
            LIMIT 1
        ) cr_try ON true
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) as ilk_tur_birim_fiyat_tl,
    
    -- İlk Tur Toplam Fiyat
    COALESCE((
        SELECT MIN(pol2.price_subtotal)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) as ilk_tur_toplam_fiyat,
    
    COALESCE((
        SELECT MIN(pol2.price_subtotal *
            CASE WHEN po_curr.name = 'TRY' THEN 1.0 
                 ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
            END)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_currency po_curr ON po2.currency_id = po_curr.id
        LEFT JOIN LATERAL (
            SELECT rate
            FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND (company_id = po2.company_id OR company_id IS NULL)
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ) cr ON true
        LEFT JOIN LATERAL (
            SELECT rate
            FROM res_currency_rate cr_t
            JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
            WHERE cr_t.currency_id = comp.currency_id
            AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
            AND cr_t.name <= CURRENT_DATE
            ORDER BY cr_t.name DESC
            LIMIT 1
        ) cr_try ON true
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) as ilk_tur_toplam_fiyat_tl,
    
    -- ============================================================================
    -- MEVCUT TUR FİYATLAR (Current Round)
    -- ============================================================================
    
    -- Mevcut Tur Birim Fiyat (önce purchase/done, yoksa en düşük teklif)
    COALESCE(
        (
            SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ),
        (
            SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ),
        0
    ) as mevcut_tur_birim_fiyat,
    
    COALESCE(
        (
            SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ),
        (
            SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ),
        0
    ) as mevcut_tur_birim_fiyat_tl,
    
    -- Mevcut Tur Toplam Fiyat (önce purchase/done, yoksa en düşük teklif)
    COALESCE(
        (
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ),
        (
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ),
        0
    ) as mevcut_tur_toplam_fiyat,
    
    COALESCE(
        (
            SELECT MIN(pol2.price_subtotal *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ),
        (
            SELECT MIN(pol2.price_subtotal *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ),
        0
    ) as mevcut_tur_toplam_fiyat_tl,
    
    -- ============================================================================
    -- SAVING METRIKLERI (İlk Tur - Mevcut Tur)
    -- ============================================================================
    
    COALESCE((
        SELECT MIN(pol2.price_subtotal)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) - COALESCE(
        (
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ),
        (
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ),
        0
    ) as saving_tutar,
    
    COALESCE((
        SELECT MIN(pol2.price_subtotal *
            CASE WHEN po_curr.name = 'TRY' THEN 1.0 
                 ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0) 
            END)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_currency po_curr ON po2.currency_id = po_curr.id
        LEFT JOIN LATERAL (
            SELECT rate
            FROM res_currency_rate
            WHERE currency_id = po2.currency_id
            AND (company_id = po2.company_id OR company_id IS NULL)
            AND name <= CURRENT_DATE
            ORDER BY name DESC
            LIMIT 1
        ) cr ON true
        LEFT JOIN LATERAL (
            SELECT rate
            FROM res_currency_rate cr_t
            JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
            WHERE cr_t.currency_id = comp.currency_id
            AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
            AND cr_t.name <= CURRENT_DATE
            ORDER BY cr_t.name DESC
            LIMIT 1
        ) cr_try ON true
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = 1
        AND pol2.price_unit > 0
    ), 0) - COALESCE(
        (
            SELECT MIN(pol2.price_subtotal *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            AND pol2.price_unit > 0
        ),
        (
            SELECT MIN(pol2.price_subtotal *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
        ),
        0
    ) as saving_tutar_tl,
    
    -- ============================================================================
    -- SAVING YÜZDESİ
    -- ============================================================================
    
    CASE
        WHEN COALESCE((
            SELECT MIN(pol2.price_subtotal)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = 1
            AND pol2.price_unit > 0
        ), 0) > 0 THEN
            ROUND(((COALESCE((
                SELECT MIN(pol2.price_subtotal)
                FROM purchase_order po2
                JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                WHERE po2.tender_id = t.id
                AND pol2.product_id = tl.product_id
                AND po2.tender_round = 1
                AND pol2.price_unit > 0
            ), 0) - COALESCE(
                (
                    SELECT MIN(pol2.price_subtotal)
                    FROM purchase_order po2
                    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                    WHERE po2.tender_id = t.id
                    AND pol2.product_id = tl.product_id
                    AND po2.tender_round = t.tender_round
                    AND po2.state IN ('purchase', 'done')
                    AND pol2.price_unit > 0
                ),
                (
                    SELECT MIN(pol2.price_subtotal)
                    FROM purchase_order po2
                    JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                    WHERE po2.tender_id = t.id
                    AND pol2.product_id = tl.product_id
                    AND po2.tender_round = t.tender_round
                    AND pol2.price_unit > 0
                ),
                0
            )) / COALESCE((
                SELECT MIN(pol2.price_subtotal)
                FROM purchase_order po2
                JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
                WHERE po2.tender_id = t.id
                AND pol2.product_id = tl.product_id
                AND po2.tender_round = 1
                AND pol2.price_unit > 0
            ), 1) * 100)::numeric, 2)
        ELSE 0
    END as saving_yuzdesi,
    
    -- ============================================================================
    -- YAKINLIK ORANI (Hedef Fiyata göre)
    -- ============================================================================
    
    CASE
        WHEN tl.target_price > 0 THEN
            ROUND((COALESCE((
                SELECT MIN(pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0))
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
    
    (
        SELECT COUNT(DISTINCT po2.partner_id)
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND pol2.price_unit > 0
    ) as tedarikci_sayisi,
    
    (
        SELECT partner.name
        FROM purchase_order po2
        JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
        JOIN res_partner partner ON po2.partner_id = partner.id
        WHERE po2.tender_id = t.id
        AND pol2.product_id = tl.product_id
        AND po2.tender_round = t.tender_round
        AND pol2.price_unit > 0
        ORDER BY pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) ASC
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
    
    COALESCE(
        -- Önce purchase/done state'inde PO var mı kontrol et
        (
            SELECT pol2.price_subtotal - (COALESCE(pol2.npv_value, 0) *
                CASE WHEN npv_curr.name = po_curr.name THEN 1.0
                     ELSE COALESCE(cr_po.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_po ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = pol2.tender_line_currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_npv ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            ORDER BY pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) ASC
            LIMIT 1
        ),
        -- Yoksa mevcut turdaki en düşük teklifi al
        (
            SELECT pol2.price_subtotal - (COALESCE(pol2.npv_value, 0) *
                CASE WHEN npv_curr.name = po_curr.name THEN 1.0
                     ELSE COALESCE(cr_po.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_po ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = pol2.tender_line_currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_npv ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
            ORDER BY pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) ASC
            LIMIT 1
        ),
        0
    ) as npv_kazanci,
    
    COALESCE(
        -- Önce purchase/done state'inde PO var mı kontrol et
        (
            SELECT (pol2.price_subtotal *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_po.rate, 1.0)
                END) - (COALESCE(pol2.npv_value, 0) *
                CASE WHEN npv_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_po ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = pol2.tender_line_currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_npv ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND po2.state IN ('purchase', 'done')
            ORDER BY pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) ASC
            LIMIT 1
        ),
        -- Yoksa mevcut turdaki en düşük teklifi al
        (
            SELECT (pol2.price_subtotal *
                CASE WHEN po_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_po.rate, 1.0)
                END) - (COALESCE(pol2.npv_value, 0) *
                CASE WHEN npv_curr.name = 'TRY' THEN 1.0
                     ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END)
            FROM purchase_order po2
            JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
            JOIN res_currency po_curr ON po2.currency_id = po_curr.id
            LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = po2.currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_po ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate
                WHERE currency_id = pol2.tender_line_currency_id
                AND (company_id = po2.company_id OR company_id IS NULL)
                AND name <= CURRENT_DATE
                ORDER BY name DESC
                LIMIT 1
            ) cr_npv ON true
            LEFT JOIN LATERAL (
                SELECT rate
                FROM res_currency_rate cr_t
                JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                WHERE cr_t.currency_id = comp.currency_id
                AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL)
                AND cr_t.name <= CURRENT_DATE
                ORDER BY cr_t.name DESC
                LIMIT 1
            ) cr_try ON true
            WHERE po2.tender_id = t.id
            AND pol2.product_id = tl.product_id
            AND po2.tender_round = t.tender_round
            AND pol2.price_unit > 0
            ORDER BY pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) ASC
            LIMIT 1
        ),
        0
    ) as npv_kazanci_tl,
    
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
    INNER JOIN ak_tender_line tl ON tl.tender_id = t.id
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
    
    -- Latest Exchange Rate for Tender Currency (Odoo's company_rate formula)
    LEFT JOIN LATERAL (
        SELECT
            CASE 
                WHEN curr.name = 'TRY' THEN 1.0 
                ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
            END as rate,
            cr.name
        FROM res_currency_rate cr
        LEFT JOIN LATERAL (
            SELECT rate
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
    
    -- Latest Exchange Rate for Line Currency (Odoo's company_rate formula)
    LEFT JOIN LATERAL (
        SELECT
            CASE 
                WHEN line_curr.name = 'TRY' THEN 1.0
                ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
            END as rate,
            cr.name
        FROM res_currency_rate cr
        LEFT JOIN LATERAL (
            SELECT rate
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
