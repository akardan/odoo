-- ============================================================================
-- NPV KAZANCI ALANLARINA ONAYLI TEDARİKÇİ ÖNCELİĞİ EKLEME
-- ============================================================================
-- Bu script, npv_kazanci ve npv_kazanci_tl alanlarına onaylı tedarikçi 
-- önceliği ekler.
--
-- Öncelik Sırası (4 seviye):
-- 1. Purchase/Done state'inde onaylı tedarikçilerden en düşük
-- 2. Purchase/Done state'inde tüm tedarikçilerden en düşük
-- 3. Mevcut turdaki onaylı tedarikçilerden en düşük
-- 4. Mevcut turdaki tüm tedarikçilerden en düşük
--
-- KULLANIM:
-- Bu dosyayı view_dashboard_detail.sql dosyasındaki npv_kazanci alanlarını
-- manuel olarak güncellemek için referans olarak kullanın.
-- ============================================================================

-- NPV Kazancı için onaylı tedarikçi kontrolü ekleme örneği:

/*
COALESCE(
    -- 1. Purchase/Done state'inde onaylı tedarikçilerden en düşük
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
        AND EXISTS (
            SELECT 1
            FROM product_supplierinfo psi
            WHERE psi.partner_id = po2.partner_id
            AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
            AND psi.is_approved = true
        )
        ORDER BY pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) ASC
        LIMIT 1
    ),
    -- 2. Purchase/Done state'inde tüm tedarikçilerden en düşük
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
    -- 3. Mevcut turdaki onaylı tedarikçilerden en düşük
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
        AND EXISTS (
            SELECT 1
            FROM product_supplierinfo psi
            WHERE psi.partner_id = po2.partner_id
            AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
            AND psi.is_approved = true
        )
        ORDER BY pol2.price_unit * (1 - COALESCE(pol2.discount, 0) / 100.0) ASC
        LIMIT 1
    ),
    -- 4. Mevcut turdaki tüm tedarikçilerden en düşük
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
) as npv_kazanci
*/

-- NOT: npv_kazanci_tl için de aynı mantık uygulanmalı, sadece TL dönüşümü eklenmelidir.
-- Yukarıdaki örnekte EXISTS kontrolü eklenen kısımlar:
--
-- AND EXISTS (
--     SELECT 1
--     FROM product_supplierinfo psi
--     WHERE psi.partner_id = po2.partner_id
--     AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id)
--     AND psi.is_approved = true
-- )
