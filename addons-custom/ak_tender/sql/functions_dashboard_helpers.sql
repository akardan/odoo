-- ============================================================================
-- DASHBOARD HELPER FUNCTIONS
-- ============================================================================
-- Bu fonksiyonlar view_dashboard_detail view'ında kullanılan tekrarlayan
-- hesaplamaları optimize eder ve kodu daha okunabilir hale getirir.
-- ============================================================================

-- ============================================================================
-- FUNCTION 1: Onaylı Tedarikçi Kontrolü
-- ============================================================================
CREATE OR REPLACE FUNCTION is_approved_supplier(
    p_partner_id INTEGER,
    p_product_id INTEGER,
    p_product_tmpl_id INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM product_supplierinfo psi
        WHERE psi.partner_id = p_partner_id
        AND (psi.product_id = p_product_id OR psi.product_tmpl_id = p_product_tmpl_id)
        AND psi.is_approved = true
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_approved_supplier IS 'Tedarikçinin onaylı olup olmadığını kontrol eder';

-- ============================================================================
-- FUNCTION 2: Döviz Kuru Hesaplama (TL'ye çevirme)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_currency_rate_to_try(
    p_currency_id INTEGER,
    p_company_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS NUMERIC AS $$
DECLARE
    v_currency_name TEXT;
    v_foreign_rate NUMERIC;
    v_try_rate NUMERIC;
BEGIN
    -- Para birimi adını al
    SELECT name INTO v_currency_name
    FROM res_currency
    WHERE id = p_currency_id;
    
    -- Eğer zaten TRY ise 1.0 döndür
    IF v_currency_name = 'TRY' THEN
        RETURN 1.0;
    END IF;
    
    -- Foreign currency rate
    SELECT rate INTO v_foreign_rate
    FROM res_currency_rate
    WHERE currency_id = p_currency_id
    AND (company_id = p_company_id OR company_id IS NULL)
    AND name <= p_date
    ORDER BY name DESC
    LIMIT 1;
    
    -- TRY rate (company currency)
    SELECT cr.rate INTO v_try_rate
    FROM res_currency_rate cr
    JOIN res_company comp ON comp.id = COALESCE(p_company_id, 1)
    WHERE cr.currency_id = comp.currency_id
    AND (cr.company_id = p_company_id OR cr.company_id IS NULL)
    AND cr.name <= p_date
    ORDER BY cr.name DESC
    LIMIT 1;
    
    -- Odoo formula: try_rate / foreign_rate
    RETURN COALESCE(v_try_rate, 1.0) / COALESCE(v_foreign_rate, 1.0);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_currency_rate_to_try IS 'Belirtilen para birimini TL''ye çevirmek için kur hesaplar';

-- ============================================================================
-- FUNCTION 3: İlk Tur Minimum Fiyat (Onaylı Öncelikli)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_round1_min_price(
    p_tender_id INTEGER,
    p_product_id INTEGER,
    p_product_tmpl_id INTEGER,
    p_price_type TEXT DEFAULT 'unit', -- 'unit' veya 'total'
    p_convert_to_try BOOLEAN DEFAULT FALSE
) RETURNS NUMERIC AS $$
DECLARE
    v_min_price NUMERIC;
BEGIN
    -- Önce onaylı tedarikçilerden
    IF p_convert_to_try THEN
        -- TL'ye çevirerek
        SELECT MIN(
            CASE 
                WHEN p_price_type = 'unit' THEN
                    pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                ELSE
                    pol.price_subtotal
            END * get_currency_rate_to_try(po.currency_id, po.company_id)
        ) INTO v_min_price
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = p_tender_id
        AND pol.product_id = p_product_id
        AND po.tender_round = 1
        AND pol.price_unit > 0
        AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id);
    ELSE
        -- Orijinal para biriminde
        SELECT MIN(
            CASE 
                WHEN p_price_type = 'unit' THEN
                    pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                ELSE
                    pol.price_subtotal
            END
        ) INTO v_min_price
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = p_tender_id
        AND pol.product_id = p_product_id
        AND po.tender_round = 1
        AND pol.price_unit > 0
        AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id);
    END IF;
    
    -- Onaylı tedarikçi yoksa tüm tekliflerden
    IF v_min_price IS NULL THEN
        IF p_convert_to_try THEN
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END * get_currency_rate_to_try(po.currency_id, po.company_id)
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = 1
            AND pol.price_unit > 0;
        ELSE
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = 1
            AND pol.price_unit > 0;
        END IF;
    END IF;
    
    RETURN COALESCE(v_min_price, 0);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_round1_min_price IS 'İlk tur minimum fiyatı hesaplar (onaylı tedarikçi öncelikli)';

-- ============================================================================
-- FUNCTION 4: Mevcut Tur Minimum Fiyat (4 Seviyeli Öncelik)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_current_round_min_price(
    p_tender_id INTEGER,
    p_tender_round INTEGER,
    p_product_id INTEGER,
    p_product_tmpl_id INTEGER,
    p_price_type TEXT DEFAULT 'unit', -- 'unit' veya 'total'
    p_convert_to_try BOOLEAN DEFAULT FALSE
) RETURNS NUMERIC AS $$
DECLARE
    v_min_price NUMERIC;
BEGIN
    -- 1. Purchase/Done state'inde onaylı tedarikçilerden
    IF p_convert_to_try THEN
        SELECT MIN(
            CASE 
                WHEN p_price_type = 'unit' THEN
                    pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                ELSE
                    pol.price_subtotal
            END * get_currency_rate_to_try(po.currency_id, po.company_id)
        ) INTO v_min_price
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = p_tender_id
        AND pol.product_id = p_product_id
        AND po.tender_round = p_tender_round
        AND po.state IN ('purchase', 'done')
        AND pol.price_unit > 0
        AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id);
    ELSE
        SELECT MIN(
            CASE 
                WHEN p_price_type = 'unit' THEN
                    pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                ELSE
                    pol.price_subtotal
            END
        ) INTO v_min_price
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = p_tender_id
        AND pol.product_id = p_product_id
        AND po.tender_round = p_tender_round
        AND po.state IN ('purchase', 'done')
        AND pol.price_unit > 0
        AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id);
    END IF;
    
    -- 2. Purchase/Done state'inde tüm tedarikçilerden
    IF v_min_price IS NULL THEN
        IF p_convert_to_try THEN
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END * get_currency_rate_to_try(po.currency_id, po.company_id)
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = p_tender_round
            AND po.state IN ('purchase', 'done')
            AND pol.price_unit > 0;
        ELSE
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = p_tender_round
            AND po.state IN ('purchase', 'done')
            AND pol.price_unit > 0;
        END IF;
    END IF;
    
    -- 3. Mevcut turdaki onaylı tedarikçilerden
    IF v_min_price IS NULL THEN
        IF p_convert_to_try THEN
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END * get_currency_rate_to_try(po.currency_id, po.company_id)
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = p_tender_round
            AND pol.price_unit > 0
            AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id);
        ELSE
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = p_tender_round
            AND pol.price_unit > 0
            AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id);
        END IF;
    END IF;
    
    -- 4. Mevcut turdaki tüm tedarikçilerden
    IF v_min_price IS NULL THEN
        IF p_convert_to_try THEN
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END * get_currency_rate_to_try(po.currency_id, po.company_id)
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = p_tender_round
            AND pol.price_unit > 0;
        ELSE
            SELECT MIN(
                CASE 
                    WHEN p_price_type = 'unit' THEN
                        pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0)
                    ELSE
                        pol.price_subtotal
                END
            ) INTO v_min_price
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = p_tender_id
            AND pol.product_id = p_product_id
            AND po.tender_round = p_tender_round
            AND pol.price_unit > 0;
        END IF;
    END IF;
    
    RETURN COALESCE(v_min_price, 0);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_current_round_min_price IS 'Mevcut tur minimum fiyatı hesaplar (4 seviyeli öncelik)';

-- ============================================================================
-- FUNCTION 5: NPV Kazancı Hesaplama (Onaylı Öncelikli)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_npv_gain(
    p_tender_id INTEGER,
    p_tender_round INTEGER,
    p_product_id INTEGER,
    p_product_tmpl_id INTEGER,
    p_convert_to_try BOOLEAN DEFAULT FALSE
) RETURNS NUMERIC AS $$
DECLARE
    v_npv_gain NUMERIC;
    v_price_subtotal NUMERIC;
    v_npv_value NUMERIC;
    v_po_currency_id INTEGER;
    v_npv_currency_id INTEGER;
    v_po_company_id INTEGER;
    v_po_currency_name TEXT;
    v_npv_currency_name TEXT;
    v_conversion_rate NUMERIC;
BEGIN
    -- Önce purchase/done state'inde onaylı tedarikçilerden
    SELECT 
        pol.price_subtotal,
        COALESCE(pol.npv_value, 0),
        po.currency_id,
        pol.tender_line_currency_id,
        po.company_id
    INTO 
        v_price_subtotal,
        v_npv_value,
        v_po_currency_id,
        v_npv_currency_id,
        v_po_company_id
    FROM purchase_order po
    JOIN purchase_order_line pol ON pol.order_id = po.id
    WHERE po.tender_id = p_tender_id
    AND pol.product_id = p_product_id
    AND po.tender_round = p_tender_round
    AND po.state IN ('purchase', 'done')
    AND pol.price_unit > 0
    AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id)
    ORDER BY (pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0))
    LIMIT 1;
    
    -- Purchase/done onaylı yoksa, purchase/done tümünden
    IF v_price_subtotal IS NULL THEN
        SELECT 
            pol.price_subtotal,
            COALESCE(pol.npv_value, 0),
            po.currency_id,
            pol.tender_line_currency_id,
            po.company_id
        INTO 
            v_price_subtotal,
            v_npv_value,
            v_po_currency_id,
            v_npv_currency_id,
            v_po_company_id
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = p_tender_id
        AND pol.product_id = p_product_id
        AND po.tender_round = p_tender_round
        AND po.state IN ('purchase', 'done')
        AND pol.price_unit > 0
        ORDER BY (pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0))
        LIMIT 1;
    END IF;
    
    -- Purchase/done yoksa, mevcut turdaki onaylı tedarikçilerden
    IF v_price_subtotal IS NULL THEN
        SELECT 
            pol.price_subtotal,
            COALESCE(pol.npv_value, 0),
            po.currency_id,
            pol.tender_line_currency_id,
            po.company_id
        INTO 
            v_price_subtotal,
            v_npv_value,
            v_po_currency_id,
            v_npv_currency_id,
            v_po_company_id
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = p_tender_id
        AND pol.product_id = p_product_id
        AND po.tender_round = p_tender_round
        AND pol.price_unit > 0
        AND is_approved_supplier(po.partner_id, p_product_id, p_product_tmpl_id)
        ORDER BY (pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0))
        LIMIT 1;
    END IF;
    
    -- Onaylı yoksa, mevcut turdaki tüm tekliflerden
    IF v_price_subtotal IS NULL THEN
        SELECT 
            pol.price_subtotal,
            COALESCE(pol.npv_value, 0),
            po.currency_id,
            pol.tender_line_currency_id,
            po.company_id
        INTO 
            v_price_subtotal,
            v_npv_value,
            v_po_currency_id,
            v_npv_currency_id,
            v_po_company_id
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = p_tender_id
        AND pol.product_id = p_product_id
        AND po.tender_round = p_tender_round
        AND pol.price_unit > 0
        ORDER BY (pol.price_unit * (1 - COALESCE(pol.discount, 0) / 100.0))
        LIMIT 1;
    END IF;
    
    -- Hiç teklif yoksa 0 döndür
    IF v_price_subtotal IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Para birimi adlarını al
    SELECT name INTO v_po_currency_name FROM res_currency WHERE id = v_po_currency_id;
    SELECT name INTO v_npv_currency_name FROM res_currency WHERE id = v_npv_currency_id;
    
    -- NPV değerini PO para birimine çevir
    IF v_po_currency_name = v_npv_currency_name THEN
        v_conversion_rate := 1.0;
    ELSE
        v_conversion_rate := get_currency_rate_to_try(v_po_currency_id, v_po_company_id) / 
                            get_currency_rate_to_try(v_npv_currency_id, v_po_company_id);
    END IF;
    
    -- NPV kazancını hesapla
    v_npv_gain := v_price_subtotal - (v_npv_value * v_conversion_rate);
    
    -- TL'ye çevir (istenirse)
    IF p_convert_to_try THEN
        v_npv_gain := v_npv_gain * get_currency_rate_to_try(v_po_currency_id, v_po_company_id);
    END IF;
    
    RETURN COALESCE(v_npv_gain, 0);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_npv_gain IS 'NPV kazancını hesaplar (onaylı tedarikçi öncelikli, 4 seviye)';

-- ============================================================================
-- KULLANIM ÖRNEKLERİ
-- ============================================================================

/*
-- İlk tur birim fiyat
SELECT get_round1_min_price(1, 100, 50, 'unit', false);

-- İlk tur birim fiyat TL
SELECT get_round1_min_price(1, 100, 50, 'unit', true);

-- İlk tur toplam fiyat
SELECT get_round1_min_price(1, 100, 50, 'total', false);

-- İlk tur toplam fiyat TL
SELECT get_round1_min_price(1, 100, 50, 'total', true);

-- Mevcut tur birim fiyat
SELECT get_current_round_min_price(1, 2, 100, 50, 'unit', false);

-- Mevcut tur birim fiyat TL
SELECT get_current_round_min_price(1, 2, 100, 50, 'unit', true);

-- Mevcut tur toplam fiyat
SELECT get_current_round_min_price(1, 2, 100, 50, 'total', false);

-- Mevcut tur toplam fiyat TL
SELECT get_current_round_min_price(1, 2, 100, 50, 'total', true);

-- NPV kazancı
SELECT get_npv_gain(1, 2, 100, 50, false);

-- NPV kazancı TL
SELECT get_npv_gain(1, 2, 100, 50, true);

-- Onaylı tedarikçi kontrolü
SELECT is_approved_supplier(10, 100, 50);

-- Döviz kuru
SELECT get_currency_rate_to_try(2, 1);
*/
