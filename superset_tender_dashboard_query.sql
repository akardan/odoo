-- Superset Dashboard için Tender ve Tender Line Analiz Sorgusu
-- Bu sorgu tender'ları, kalemlerini ve ilgili boyutları içerir

SELECT 
    -- Tender Bilgileri
    t.id as tender_id,
    t.code as tender_code,
    t.name as tender_name,
    t.tender_type,
    CASE 
        WHEN t.tender_type = 'direct' THEN 'Direkt'
        WHEN t.tender_type = 'indirect' THEN 'Endirekt'
        WHEN t.tender_type = 'mice' THEN 'MICE'
        WHEN t.tender_type = 'promotion' THEN 'Promosyon/Kırtasiye'
    END as tender_type_label,
    
    -- Tarih Bilgileri
    t.start_date,
    t.end_date,
    t.request_date,
    t.required_delivery_date,
    DATE_PART('day', t.end_date - t.start_date) as tender_duration_days,
    
    -- Workflow Bilgileri
    COALESCE((ws.name::jsonb)->>'tr_TR', (ws.name::jsonb)->>'en_US', ws.name::text) as workflow_state,
    ws.code as workflow_state_code,
    wd.name as workflow_definition,
    t.workflow_start_date,
    t.workflow_end_date,
    
    -- Satın Alma Uzmanı
    u.login as buyer_email,
    p.name as buyer_name,
    
    -- Coğrafi Bilgiler
    country.name as country,
    state.name as state,
    t.city,
    
    -- Hedef Bilgileri
    t.target_type,
    CASE
        WHEN t.target_type = 'price' THEN 'Fiyat'
        WHEN t.target_type = 'discount' THEN 'İndirim'
        ELSE t.target_type
    END as target_type_label,
    t.target_price,
    t.target_discount,
    curr.name as currency,
    
    -- Aciliyet Bilgileri
    t.is_urgent,
    t.urgent_reason,
    t.urgent_deadline,
    
    -- Toplu Satın Alma
    t.is_bulk_purchase,
    t.related_pr_ids,
    
    -- ERP Entegrasyon
    t.erp_pr_id,
    t.erp_company_code,
    t.erp_plant_code,
    t.erp_requester,
    
    -- Tender Line Bilgileri
    tl.id as line_id,
    tl.sequence as line_sequence,
    tl.display_type,
    tl.name as line_description,
    
    -- Ürün Bilgileri
    pp.id as product_id,
    pp.default_code as product_code,
    COALESCE((pt.name::jsonb)->>'tr_TR', (pt.name::jsonb)->>'en_US', pt.name::text) as product_name,
    pc.complete_name as product_category,
    
    -- Miktar ve Birim
    tl.quantity,
    tl.days,
    COALESCE((uom.name::jsonb)->>'tr_TR', (uom.name::jsonb)->>'en_US', uom.name::text) as uom,
    
    -- Fiyat Bilgileri
    tl.target_price as line_target_price,
    tl.target_discount as line_target_discount,
    (tl.quantity * tl.target_price) as line_total_target,
    (tl.quantity * tl.days * tl.target_price) as line_total_with_days,
    
    -- Teslimat Bilgileri
    tl.required_delivery_date as line_delivery_date,
    tl.lead_time_days,
    
    -- Özellikler
    tl.required as is_required,
    tl.allow_alternative,
    
    -- Otel Bilgileri (MICE için)
    hotel.name as hotel_name,
    hotel.hotel_star_rating,
    
    -- Teklif Sayıları
    (SELECT COUNT(*) FROM purchase_order po WHERE po.tender_id = t.id) as total_offers,
    (SELECT COUNT(*) FROM purchase_order po WHERE po.tender_id = t.id AND po.tender_round = t.tender_round) as current_round_offers,
    t.tender_round,
    
    -- Kazanan Teklifler
    (SELECT COUNT(*) 
     FROM purchase_order po 
     WHERE po.tender_id = t.id 
     AND po.state IN ('purchase', 'done')) as winning_offers_count,
    
    -- Oluşturma ve Güncelleme Bilgileri
    t.create_date as tender_create_date,
    t.write_date as tender_update_date,
    creator.login as created_by,
    updater.login as updated_by,
    
    -- Hesaplanan Alanlar
    CASE 
        WHEN t.end_date < NOW() THEN 'Süresi Dolmuş'
        WHEN t.start_date > NOW() THEN 'Başlamamış'
        ELSE 'Aktif'
    END as tender_status,
    
    DATE_PART('day', NOW() - t.start_date) as days_since_start,
    DATE_PART('day', t.end_date - NOW()) as days_until_end,
    
    -- Yıl, Ay, Çeyrek (Zaman Analizi için)
    EXTRACT(YEAR FROM t.start_date) as year,
    EXTRACT(MONTH FROM t.start_date) as month,
    EXTRACT(QUARTER FROM t.start_date) as quarter,
    TO_CHAR(t.start_date, 'YYYY-MM') as year_month,
    TO_CHAR(t.start_date, 'Day') as day_of_week

FROM 
    ak_tender t
    
    -- Tender Lines
    LEFT JOIN ak_tender_line tl ON tl.tender_id = t.id
    
    -- Product Information
    LEFT JOIN product_product pp ON tl.product_id = pp.id
    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
    LEFT JOIN product_category pc ON pt.categ_id = pc.id
    LEFT JOIN uom_uom uom ON tl.uom_id = uom.id
    
    -- Workflow Information
    LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
    LEFT JOIN ak_workflow_definition wd ON t.workflow_definition_id = wd.id
    
    -- User Information
    LEFT JOIN res_users u ON t.buyer_id = u.id
    LEFT JOIN res_partner p ON u.partner_id = p.id
    
    -- Geographic Information
    LEFT JOIN res_country country ON t.country_id = country.id
    LEFT JOIN res_country_state state ON t.state_id = state.id
    
    -- Currency
    LEFT JOIN res_currency curr ON t.currency_id = curr.id
    
    -- Hotel Information (for MICE)
    LEFT JOIN res_partner hotel ON tl.hotel_partner_id = hotel.id
    
    -- Creator and Updater
    LEFT JOIN res_users creator ON t.create_uid = creator.id
    LEFT JOIN res_users updater ON t.write_uid = updater.id

WHERE 
    -- Sadece ürün satırlarını dahil et (section ve note hariç)
    (tl.display_type = 'product' OR tl.display_type IS NULL)
    
ORDER BY 
    t.start_date DESC,
    t.id DESC,
    tl.sequence ASC;


-- Alternatif: Özet Sorgu (Tender Bazında Toplu Veriler)
-- Bu sorgu her tender için özet bilgiler verir

/*
SELECT 
    t.id as tender_id,
    t.code as tender_code,
    t.name as tender_name,
    t.tender_type,
    t.start_date,
    t.end_date,
    ws.name as workflow_state,
    u.login as buyer_email,
    p.name as buyer_name,
    
    -- Toplam İstatistikler
    COUNT(DISTINCT tl.id) FILTER (WHERE tl.display_type = 'product') as total_line_items,
    SUM(tl.quantity) FILTER (WHERE tl.display_type = 'product') as total_quantity,
    SUM(tl.quantity * tl.target_price) FILTER (WHERE tl.display_type = 'product') as total_target_amount,
    
    -- Teklif İstatistikleri
    COUNT(DISTINCT po.id) as total_offers,
    COUNT(DISTINCT po.partner_id) as unique_suppliers,
    
    -- Tarih Hesaplamaları
    DATE_PART('day', t.end_date - t.start_date) as duration_days,
    CASE 
        WHEN t.end_date < NOW() THEN 'Süresi Dolmuş'
        WHEN t.start_date > NOW() THEN 'Başlamamış'
        ELSE 'Aktif'
    END as status,
    
    -- Zaman Boyutları
    EXTRACT(YEAR FROM t.start_date) as year,
    EXTRACT(MONTH FROM t.start_date) as month,
    EXTRACT(QUARTER FROM t.start_date) as quarter

FROM 
    ak_tender t
    LEFT JOIN ak_tender_line tl ON tl.tender_id = t.id
    LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
    LEFT JOIN res_users u ON t.buyer_id = u.id
    LEFT JOIN res_partner p ON u.partner_id = p.id
    LEFT JOIN purchase_order po ON po.tender_id = t.id

GROUP BY 
    t.id, t.code, t.name, t.tender_type, t.start_date, t.end_date,
    ws.name, u.login, p.name

ORDER BY 
    t.start_date DESC;
*/