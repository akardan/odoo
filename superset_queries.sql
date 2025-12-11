-- ============================================================================
-- SUPERSET DASHBOARD QUERIES
-- İhale (Tender) ve Workflow Transition History için PostgreSQL Sorguları
-- ============================================================================
-- Tablo isim konvansiyonları:
-- t = ak_tender, tl = ak_tender_line, wth = ak_workflow_transition_history
-- ws = ak_workflow_state, wt = ak_workflow_transition, u = res_users
-- pp = product_product, pt = product_template, pc = product_category
-- ============================================================================


-- ============================================================================
-- KULLANIM TALİMATLARI / USAGE INSTRUCTIONS
-- ============================================================================

/*
SUPERSET DASHBOARD VIEW'LARI:

📊 SATINALMACI PERFORMANS RAPORU İÇİN (Buyer Performance Dashboard):
   - view_buyer_performance_dataset → Ana KPI kartları ve metrikler için
   - view_buyer_tender_detail → Alt tablo (İhale Performans Özeti) için
   - view_buyer_monthly_trend → Zaman serisi grafikleri için

🎯 GENEL İHALE RAPORLARI İÇİN:
   1. view_tender_summary → İhale özet raporları, KPI kartları
   2. view_tender_lines_detail → Ürün bazlı analizler, kalem detayları
   3. view_workflow_transition_history → Workflow akış analizleri
   4. view_tender_performance → İhale performans, SLA takibi
   5. view_state_statistics → Durum bazlı KPI'lar, bottleneck tespiti
   6. view_user_performance → Kullanıcı performans raporları

SUPERSET'TE KULLANIM:
1. Data → Datasets → + Dataset
2. View seçin (örn: view_buyer_performance_dataset)
3. Charts menüsünden yeni chart oluşturun
4. Dashboard'a ekleyin

PERFORMANS İPUCU:
- Büyük veri setleri için WHERE ile filtreleme yapın
- Zaman aralığı filtresi ekleyin (year_month, year vb.)
- Materialized View kullanmayı düşünün (büyük tablolar için)
*/


DROP VIEW IF EXISTS view_tender_summary CASCADE;

CREATE VIEW view_tender_summary AS
    -- ============================================================================
    -- 1. İHALE ÖZET SORGUSU (TENDER SUMMARY QUERY)
    -- ============================================================================
    -- Bu sorgu ihale ana verilerini, durum bilgilerini ve istatistikleri getirir
    -- This query retrieves main tender data, state information and statistics

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
            ELSE t.tender_type
        END as tender_type_label,
        
        -- Tarih Bilgileri
        t.start_date,
        t.end_date,
        t.request_date,
        t.required_delivery_date,
        DATE_PART('day', t.end_date - t.start_date) as tender_duration_days,
        
        -- Workflow Bilgileri
        t.workflow_current_state_id as workflow_state_id,
        COALESCE((ws.name::jsonb)->>'tr_TR', (ws.name::jsonb)->>'en_US', ws.name::text) as workflow_state,
        ws.code as workflow_state_code,
        t.workflow_definition_id,
        COALESCE((wd.name::jsonb)->>'tr_TR', (wd.name::jsonb)->>'en_US', wd.name::text) as workflow_definition,
        t.workflow_start_date,
        t.workflow_end_date,
        
        -- Satın Alma Uzmanı
        t.buyer_id,
        buyer_user.login as buyer_email,
        buyer_partner.name as buyer_name,
        
        -- Coğrafi Bilgiler
        t.country_id,
        country.name as country,
        t.state_id,
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
        t.currency_id,
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
        
        -- Teklif Bilgileri
        (SELECT COUNT(*) FROM purchase_order po WHERE po.tender_id = t.id) as total_offers,
        (SELECT COUNT(*) FROM purchase_order po WHERE po.tender_id = t.id AND po.tender_round = t.tender_round) as current_round_offers,
        t.tender_round,
        
        -- Kazanan Teklifler
        (SELECT COUNT(*)
        FROM purchase_order po
        WHERE po.tender_id = t.id
        AND po.state IN ('purchase', 'done')) as winning_offers_count,
        
        -- Line istatistikleri
        (SELECT COUNT(*)
        FROM ak_tender_line tl
        WHERE tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)) as line_count,
        
        (SELECT COALESCE(SUM(tl.quantity), 0)
        FROM ak_tender_line tl
        WHERE tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)) as total_quantity,
        
        -- Workflow geçiş sayısı
        (SELECT COUNT(*)
        FROM ak_workflow_transition_history wth
        WHERE wth.res_model = 'ak.tender'
        AND wth.res_id = t.id) as transition_count,
        
        -- Oluşturma ve Güncelleme
        t.create_date as tender_create_date,
        t.write_date as tender_update_date,
        t.create_uid,
        creator.login as created_by,
        t.write_uid,
        updater.login as updated_by,
        
        -- Hesaplanan Durum
        CASE
            WHEN t.end_date < NOW() THEN 'Süresi Dolmuş'
            WHEN t.start_date > NOW() THEN 'Başlamamış'
            ELSE 'Aktif'
        END as tender_status,
        
        DATE_PART('day', NOW() - t.start_date) as days_since_start,
        DATE_PART('day', t.end_date - NOW()) as days_until_end,
        
        -- Zaman Analizi Alanları
        EXTRACT(YEAR FROM t.start_date) as year,
        EXTRACT(MONTH FROM t.start_date) as month,
        EXTRACT(QUARTER FROM t.start_date) as quarter,
        TO_CHAR(t.start_date, 'YYYY-MM') as year_month,
        TO_CHAR(t.start_date, 'Day') as day_of_week

    FROM ak_tender t
        -- Workflow
        LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
        LEFT JOIN ak_workflow_definition wd ON t.workflow_definition_id = wd.id
        
        -- Buyer
        LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
        LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
        
        -- Geography
        LEFT JOIN res_country country ON t.country_id = country.id
        LEFT JOIN res_country_state state ON t.state_id = state.id
        
        -- Currency
        LEFT JOIN res_currency curr ON t.currency_id = curr.id
        
        -- Creators
        LEFT JOIN res_users creator ON t.create_uid = creator.id
        LEFT JOIN res_users updater ON t.write_uid = updater.id

    ORDER BY t.start_date DESC, t.id DESC;

DROP VIEW IF EXISTS view_tender_lines_detail CASCADE;

CREATE VIEW view_tender_lines_detail AS
    -- ============================================================================
    -- 2. İHALE KALEMLERİ DETAY SORGUSU (TENDER LINES DETAIL QUERY)
    -- ============================================================================
    -- Bu sorgu ihale kalemlerinin detaylı bilgilerini getirir
    -- This query retrieves detailed information about tender line items

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
            ELSE t.tender_type
        END as tender_type_label,
        
        -- Tarih Bilgileri
        t.start_date,
        t.end_date,
        t.request_date,
        t.required_delivery_date,
        
        -- Workflow Bilgileri
        COALESCE((ws.name::jsonb)->>'tr_TR', (ws.name::jsonb)->>'en_US', ws.name::text) as workflow_state,
        ws.code as workflow_state_code,
        COALESCE((wd.name::jsonb)->>'tr_TR', (wd.name::jsonb)->>'en_US', wd.name::text) as workflow_definition,
        
        -- Satın Alma Uzmanı
        buyer_user.login as buyer_email,
        buyer_partner.name as buyer_name,
        
        -- Coğrafi Bilgiler
        country.name as country,
        state.name as state,
        t.city,
        
        -- Hedef Bilgileri (Tender Level)
        t.target_type,
        CASE
            WHEN t.target_type = 'price' THEN 'Fiyat'
            WHEN t.target_type = 'discount' THEN 'İndirim'
            ELSE t.target_type
        END as target_type_label,
        curr.name as currency,
        
        -- ERP Bilgiler
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
        
        -- Hedef Tipi ve İskonto / Target Type and Discount
        tl.target_type as line_target_type,
        CASE
            WHEN tl.target_type = 'price' THEN 'Fiyat'
            WHEN tl.target_type = 'discount' THEN 'İndirim'
            ELSE tl.target_type
        END as line_target_type_label,
        tl.target_price as line_target_price,
        tl.target_discount as line_target_discount,

        -- Fiyat Bilgileri (Line Level)
        (tl.quantity * tl.target_price * (1 - tl.target_discount)) as line_total_target,
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
        TO_CHAR(t.start_date, 'Day') as day_of_week,
        prl.material_group as product_material_group,
        prl.purchasing_group as product_purchasing_group,
        
        -- Line Para Birimi / Line Currency
        tl.currency_id as line_currency_id,
        line_curr.name as line_currency,
        line_curr.symbol as line_currency_symbol
        
    FROM ak_tender t
        -- Tender Lines
        INNER JOIN ak_tender_line tl ON tl.tender_id = t.id
        
        -- Product Information
        LEFT JOIN product_product pp ON tl.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        LEFT JOIN product_category pc ON pt.categ_id = pc.id
        LEFT JOIN uom_uom uom ON tl.uom_id = uom.id
        
        -- Purchase Requisition Line Information
        LEFT JOIN purchase_requisition_line prl ON tl.id = prl.tender_line_id

        -- Workflow Information
        LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
        LEFT JOIN ak_workflow_definition wd ON t.workflow_definition_id = wd.id
        
        -- User Information
        LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
        LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
        
        -- Geographic Information
        LEFT JOIN res_country country ON t.country_id = country.id
        LEFT JOIN res_country_state state ON t.state_id = state.id
        
        -- Currency
        LEFT JOIN res_currency curr ON t.currency_id = curr.id
        LEFT JOIN res_currency line_curr ON tl.currency_id = line_curr.id
        
        -- Hotel Information (for MICE)
        LEFT JOIN res_partner hotel ON tl.hotel_partner_id = hotel.id
        
        -- Creator and Updater
        LEFT JOIN res_users creator ON t.create_uid = creator.id
        LEFT JOIN res_users updater ON t.write_uid = updater.id

    WHERE (tl.display_type = 'product' OR tl.display_type IS NULL)
    ORDER BY t.start_date DESC, t.id DESC, tl.sequence ASC;


DROP VIEW IF EXISTS view_workflow_transition_history CASCADE;

CREATE VIEW view_workflow_transition_history AS
    -- ============================================================================
    -- 3. WORKFLOW GEÇİŞ GEÇMİŞİ SORGUSU (WORKFLOW TRANSITION HISTORY QUERY)
    -- ============================================================================
    -- Bu sorgu workflow geçiş geçmişini detaylı şekilde getirir
    -- This query retrieves detailed workflow transition history

    SELECT
        -- History Record Info
        wth.id as history_id,
        wth.res_model,
        wth.res_id,
        wth.create_date as transition_date,
        
        -- İhale Bilgileri (eğer tender ise)
        CASE WHEN wth.res_model = 'ak.tender' THEN t.id ELSE NULL END as tender_id,
        CASE WHEN wth.res_model = 'ak.tender' THEN t.code ELSE NULL END as tender_code,
        CASE WHEN wth.res_model = 'ak.tender' THEN t.name ELSE NULL END as tender_name,
        CASE WHEN wth.res_model = 'ak.tender' THEN t.tender_type ELSE NULL END as tender_type,
        CASE
            WHEN wth.res_model = 'ak.tender' AND t.tender_type = 'direct' THEN 'Direkt'
            WHEN wth.res_model = 'ak.tender' AND t.tender_type = 'indirect' THEN 'Endirekt'
            WHEN wth.res_model = 'ak.tender' AND t.tender_type = 'mice' THEN 'MICE'
            WHEN wth.res_model = 'ak.tender' AND t.tender_type = 'promotion' THEN 'Promosyon/Kırtasiye'
            ELSE NULL
        END as tender_type_label,
        
        -- FROM State Bilgileri
        wth.from_state_id,
        COALESCE((fs.name::jsonb)->>'tr_TR', (fs.name::jsonb)->>'en_US', fs.name::text) as from_state_name,
        fs.code as from_state_code,
        fs.sequence as from_state_sequence,
        
        -- TO State Bilgileri
        wth.to_state_id,
        COALESCE((ts.name::jsonb)->>'tr_TR', (ts.name::jsonb)->>'en_US', ts.name::text) as to_state_name,
        ts.code as to_state_code,
        ts.sequence as to_state_sequence,
        
        -- Geçiş Bilgileri
        wth.transition_id,
        COALESCE((wt.name::jsonb)->>'tr_TR', (wt.name::jsonb)->>'en_US', wt.name::text) as transition_name,
        wt.code as transition_code,
        
        -- Aşama Bilgileri
        wth.stage_id,
        COALESCE((wts.name::jsonb)->>'tr_TR', (wts.name::jsonb)->>'en_US', wts.name::text) as stage_name,
        wts.sequence as stage_sequence,
        
        -- Kullanıcı Bilgileri
        wth.user_id,
        p.name as user_name,
        u.login as user_login,
        
        -- Durum
        wth.status,
        CASE
            WHEN wth.status = 'pending' THEN 'Beklemede'
            WHEN wth.status = 'completed' THEN 'Tamamlandı'
            WHEN wth.status = 'failed' THEN 'Başarısız'
            ELSE wth.status
        END as status_label,
        wth.comment,
        
        -- Zaman Bilgileri (Hours)
        wth.start_time,
        wth.end_time,
        wth.elapsed_time as elapsed_hours,
        wth.elapsed_time_display,
        wth.expected_duration as expected_hours,
        (wth.elapsed_time - wth.expected_duration) as duration_variance_hours,
        
        -- Gecikme Analizi
        CASE
            WHEN wth.elapsed_time > wth.expected_duration AND wth.expected_duration > 0 THEN 'Gecikmeli'
            WHEN wth.elapsed_time <= wth.expected_duration AND wth.expected_duration > 0 THEN 'Zamanında'
            ELSE 'Hedef Yok'
        END as timing_status,
        
        CASE
            WHEN wth.expected_duration > 0
            THEN ROUND(((wth.elapsed_time - wth.expected_duration) / wth.expected_duration * 100)::numeric, 2)
            ELSE 0
        END as delay_percentage,
        
        -- Zaman Analizi Alanları
        EXTRACT(YEAR FROM wth.create_date) as year,
        EXTRACT(MONTH FROM wth.create_date) as month,
        EXTRACT(QUARTER FROM wth.create_date) as quarter,
        EXTRACT(WEEK FROM wth.create_date) as week,
        EXTRACT(DOW FROM wth.create_date) as day_of_week,
        EXTRACT(HOUR FROM wth.create_date) as hour,
        TO_CHAR(wth.create_date, 'YYYY-MM') as year_month,
        TO_CHAR(wth.create_date, 'YYYY-"W"IW') as year_week,
        TO_CHAR(wth.create_date, 'Day') as day_name

    FROM ak_workflow_transition_history wth
        -- Tender Info (if applicable)
        LEFT JOIN ak_tender t ON (wth.res_model = 'ak.tender' AND wth.res_id = t.id)
        
        -- States
        LEFT JOIN ak_workflow_state fs ON wth.from_state_id = fs.id
        LEFT JOIN ak_workflow_state ts ON wth.to_state_id = ts.id
        
        -- Transition
        LEFT JOIN ak_workflow_transition wt ON wth.transition_id = wt.id
        
        -- Stage
        LEFT JOIN ak_workflow_transition_stage wts ON wth.stage_id = wts.id
        
        -- User
        LEFT JOIN res_users u ON wth.user_id = u.id
        LEFT JOIN res_partner p ON u.partner_id = p.id

    ORDER BY wth.create_date DESC;


DROP VIEW IF EXISTS view_tender_performance CASCADE;

CREATE VIEW view_tender_performance AS
    -- ============================================================================
    -- 4. İHALE PERFORMANS ANALİZİ (TENDER PERFORMANCE ANALYSIS)
    -- ============================================================================
    -- İhalelerin workflow'daki performansını analiz eder
    -- Analyzes tender performance in workflow

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
            ELSE t.tender_type
        END as tender_type_label,
        
        -- Tarih Bilgileri
        t.start_date,
        t.end_date,
        t.request_date,
        t.required_delivery_date,
        t.create_date as tender_create_date,
        t.write_date as tender_update_date,
        
        -- Mevcut Workflow Durumu
        t.workflow_current_state_id as workflow_state_id,
        COALESCE((ws.name::jsonb)->>'tr_TR', (ws.name::jsonb)->>'en_US', ws.name::text) as workflow_state,
        ws.code as workflow_state_code,
        
        -- Para Birimi ve Hedef
        t.currency_id,
        curr.name as currency,
        t.target_price,
        t.target_type,
        
        -- Buyer Bilgileri
        t.buyer_id,
        buyer_user.login as buyer_email,
        buyer_partner.name as buyer_name,
        
        -- Workflow Performans Metrikleri
        COUNT(DISTINCT wth.id) as transition_count,
        SUM(CASE WHEN wth.status = 'completed' THEN 1 ELSE 0 END) as completed_transitions,
        SUM(CASE WHEN wth.status = 'pending' THEN 1 ELSE 0 END) as pending_transitions,
        SUM(CASE WHEN wth.status = 'failed' THEN 1 ELSE 0 END) as failed_transitions,
        
        -- Süre Metrikleri (Hours)
        SUM(wth.elapsed_time) as total_elapsed_hours,
        AVG(wth.elapsed_time) as avg_transition_hours,
        MIN(wth.elapsed_time) as min_transition_hours,
        MAX(wth.elapsed_time) as max_transition_hours,
        SUM(wth.expected_duration) as total_expected_hours,
        SUM(wth.elapsed_time - wth.expected_duration) as total_delay_hours,
        
        -- Geçiş Tarihleri
        MIN(wth.create_date) as first_transition_date,
        MAX(wth.create_date) as last_transition_date,
        t.workflow_start_date,
        t.workflow_end_date,
        
        -- Hesaplanmış Metrikler
        DATE_PART('day', t.end_date - t.start_date) as tender_duration_days,
        DATE_PART('day', NOW() - t.start_date) as days_since_start,
        DATE_PART('day', t.end_date - NOW()) as days_until_end,
        
        CASE
            WHEN t.workflow_end_date IS NOT NULL THEN
                DATE_PART('day', t.workflow_end_date - t.workflow_start_date)
            ELSE
                DATE_PART('day', NOW() - t.workflow_start_date)
        END as workflow_days,
        
        -- Durum
        CASE
            WHEN t.end_date < NOW() THEN 'Süresi Dolmuş'
            WHEN t.start_date > NOW() THEN 'Başlamamış'
            ELSE 'Aktif'
        END as tender_status,
        
        -- Başarı Oranı
        CASE
            WHEN COUNT(wth.id) > 0 THEN
                ROUND((SUM(CASE WHEN wth.status = 'completed' THEN 1 ELSE 0 END)::numeric / COUNT(wth.id)::numeric * 100), 2)
            ELSE 0
        END as success_rate_percentage,
        
        -- Zaman Analizi
        EXTRACT(YEAR FROM t.start_date) as year,
        EXTRACT(MONTH FROM t.start_date) as month,
        EXTRACT(QUARTER FROM t.start_date) as quarter,
        TO_CHAR(t.start_date, 'YYYY-MM') as year_month

    FROM ak_tender t
        -- Workflow State
        LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
        
        -- Currency
        LEFT JOIN res_currency curr ON t.currency_id = curr.id
        
        -- Buyer
        LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
        LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
        
        -- Transitions
        LEFT JOIN ak_workflow_transition_history wth ON (
            wth.res_model = 'ak.tender' AND wth.res_id = t.id
        )

    GROUP BY
        t.id, t.code, t.name, t.tender_type, t.start_date, t.end_date,
        t.request_date, t.required_delivery_date, t.create_date, t.write_date,
        t.workflow_current_state_id, t.workflow_start_date, t.workflow_end_date,
        t.currency_id, t.target_price, t.target_type, t.buyer_id,
        ws.name, ws.code, curr.name,
        buyer_user.login, buyer_partner.name
    ORDER BY t.start_date DESC, t.id DESC;


DROP VIEW IF EXISTS view_state_statistics CASCADE;

CREATE VIEW view_state_statistics AS
    -- ============================================================================
    -- 5. DURUM BAZLI İSTATİSTİKLER (STATE-BASED STATISTICS)
    -- ============================================================================
    -- Her durumdaki ihalelerin istatistiklerini gösterir
    -- Shows statistics of tenders in each state

    SELECT
        -- State Bilgileri
        ws.id as state_id,
        COALESCE((ws.name::jsonb)->>'tr_TR', (ws.name::jsonb)->>'en_US', ws.name::text) as state_name,
        ws.code as state_code,
        ws.sequence as state_sequence,
        
        -- Tender İstatistikleri
        COUNT(DISTINCT t.id) as tender_count,
        COUNT(DISTINCT CASE WHEN t.tender_type = 'direct' THEN t.id END) as direct_tender_count,
        COUNT(DISTINCT CASE WHEN t.tender_type = 'indirect' THEN t.id END) as indirect_tender_count,
        COUNT(DISTINCT CASE WHEN t.tender_type = 'mice' THEN t.id END) as mice_tender_count,
        COUNT(DISTINCT CASE WHEN t.tender_type = 'promotion' THEN t.id END) as promotion_tender_count,
        
        -- Finansal Metrikler
        SUM(t.target_price) as total_target_price,
        AVG(t.target_price) as avg_target_price,
        MAX(t.target_price) as max_target_price,
        MIN(t.target_price) as min_target_price,
        
        -- Süre Metrikleri (Hours)
        AVG(wth.elapsed_time) as avg_elapsed_hours,
        MAX(wth.elapsed_time) as max_elapsed_hours,
        MIN(wth.elapsed_time) as min_elapsed_hours,
        SUM(wth.elapsed_time) as total_elapsed_hours,
        
        -- Beklenen Süre
        ws.default_duration_days * 24 as expected_duration_hours,
        
        -- Geçiş Tarihleri
        MIN(wth.create_date) as oldest_entry_date,
        MAX(wth.create_date) as newest_entry_date,
        COUNT(wth.id) as total_transitions_to_state,
        
        -- Durum Dağılımı
        SUM(CASE WHEN wth.status = 'completed' THEN 1 ELSE 0 END) as completed_transitions,
        SUM(CASE WHEN wth.status = 'pending' THEN 1 ELSE 0 END) as pending_transitions,
        SUM(CASE WHEN wth.status = 'failed' THEN 1 ELSE 0 END) as failed_transitions,
        
        -- Başarı Oranı
        CASE
            WHEN COUNT(wth.id) > 0 THEN
                ROUND((SUM(CASE WHEN wth.status = 'completed' THEN 1 ELSE 0 END)::numeric / COUNT(wth.id)::numeric * 100), 2)
            ELSE 0
        END as success_rate_percentage,
        
        -- Gecikme Analizi
        AVG(CASE
            WHEN wth.expected_duration > 0 THEN
                (wth.elapsed_time - wth.expected_duration)
            ELSE NULL
        END) as avg_delay_hours,
        
        COUNT(CASE
            WHEN wth.elapsed_time > wth.expected_duration AND wth.expected_duration > 0
            THEN 1
        END) as delayed_transitions_count

    FROM ak_workflow_state ws
        LEFT JOIN ak_tender t ON (
            t.workflow_current_state_id = ws.id
        )
        LEFT JOIN ak_workflow_transition_history wth ON (
            wth.res_model = 'ak.tender'
            AND wth.to_state_id = ws.id
        )

    GROUP BY
        ws.id, ws.name, ws.code, ws.sequence, ws.default_duration_days
    ORDER BY ws.sequence;


DROP VIEW IF EXISTS view_user_performance CASCADE;

CREATE VIEW view_user_performance AS
    -- ============================================================================
    -- 6. KULLANICI PERFORMANSI (USER PERFORMANCE)
    -- ============================================================================
    -- Kullanıcıların workflow geçişlerindeki performansını analiz eder
    -- Analyzes user performance in workflow transitions

    SELECT
        -- Kullanıcı Bilgileri
        u.id as user_id,
        p.name as user_name,
        u.login as user_login,
        u.active as user_active,
        p.email as user_email,
        
        -- Genel Geçiş İstatistikleri
        COUNT(wth.id) as transition_count,
        SUM(CASE WHEN wth.status = 'completed' THEN 1 ELSE 0 END) as completed_count,
        SUM(CASE WHEN wth.status = 'pending' THEN 1 ELSE 0 END) as pending_count,
        SUM(CASE WHEN wth.status = 'failed' THEN 1 ELSE 0 END) as failed_count,
        
        -- Model Bazlı İstatistikler
        SUM(CASE WHEN wth.res_model = 'ak.tender' THEN 1 ELSE 0 END) as tender_transitions,
        SUM(CASE WHEN wth.res_model = 'ak.tender' AND wth.status = 'completed' THEN 1 ELSE 0 END) as tender_completed,
        
        -- Başarı Oranı
        CASE
            WHEN COUNT(wth.id) > 0 THEN
                ROUND((SUM(CASE WHEN wth.status = 'completed' THEN 1 ELSE 0 END)::numeric / COUNT(wth.id)::numeric * 100), 2)
            ELSE 0
        END as success_rate_percentage,
        
        -- Süre Metrikleri (Hours)
        AVG(wth.elapsed_time) as avg_elapsed_hours,
        MIN(wth.elapsed_time) as min_elapsed_hours,
        MAX(wth.elapsed_time) as max_elapsed_hours,
        SUM(wth.elapsed_time) as total_elapsed_hours,
        
        -- Beklenen Süre Karşılaştırması
        AVG(wth.expected_duration) as avg_expected_hours,
        AVG(wth.elapsed_time - wth.expected_duration) as avg_delay_hours,
        
        -- Gecikme Analizi
        COUNT(CASE
            WHEN wth.elapsed_time > wth.expected_duration AND wth.expected_duration > 0
            THEN 1
        END) as delayed_transitions,
        
        COUNT(CASE
            WHEN wth.elapsed_time <= wth.expected_duration AND wth.expected_duration > 0
            THEN 1
        END) as on_time_transitions,
        
        -- Tarih Bilgileri
        MIN(wth.create_date) as first_transition_date,
        MAX(wth.create_date) as last_transition_date,
        
        -- Son X Gündeki Aktiviteler
        SUM(CASE WHEN wth.create_date >= NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END) as transitions_last_7_days,
        SUM(CASE WHEN wth.create_date >= NOW() - INTERVAL '30 days' THEN 1 ELSE 0 END) as transitions_last_30_days,
        SUM(CASE WHEN wth.create_date >= NOW() - INTERVAL '90 days' THEN 1 ELSE 0 END) as transitions_last_90_days,
        
        -- Bu Ay ve Bu Yıl
        SUM(CASE
            WHEN EXTRACT(YEAR FROM wth.create_date) = EXTRACT(YEAR FROM NOW())
            AND EXTRACT(MONTH FROM wth.create_date) = EXTRACT(MONTH FROM NOW())
            THEN 1 ELSE 0
        END) as transitions_this_month,
        
        SUM(CASE
            WHEN EXTRACT(YEAR FROM wth.create_date) = EXTRACT(YEAR FROM NOW())
            THEN 1 ELSE 0
        END) as transitions_this_year,
        
        -- Ortalama Günlük Aktivite
        CASE
            WHEN MIN(wth.create_date) IS NOT NULL THEN
                ROUND((COUNT(wth.id)::numeric / GREATEST(DATE_PART('day', NOW() - MIN(wth.create_date)), 1)::numeric), 2)
            ELSE 0
        END as avg_transitions_per_day

    FROM res_users u
        LEFT JOIN res_partner p ON u.partner_id = p.id
        LEFT JOIN ak_workflow_transition_history wth ON wth.user_id = u.id

    WHERE u.active = true
    GROUP BY u.id, u.login, u.active, p.name, p.email
    HAVING COUNT(wth.id) > 0
    ORDER BY transition_count DESC;


-- ============================================================================
-- SATINALMACI PERFORMANS DASHBOARD VİEW'LARI
-- Superset'te doğrudan kullanılabilir basit dataset'ler
-- ============================================================================

DROP VIEW IF EXISTS view_buyer_performance_dataset CASCADE;

CREATE VIEW view_buyer_performance_dataset AS
-- ============================================================================
-- ANA DATASET: Satınalmacı Performans Dashboard
-- ============================================================================
-- Her satır bir ihalenin bir ürünü (tender line).
-- Superset'te filtreleme ve gruplama için optimize edilmiş.
-- Dashboard'daki tüm KPI'ları hesaplar.

SELECT
    -- ÖNCELİKLİ ANAHTARLAR / PRIMARY KEYS
    t.id as ihale_id,
    t.code as ihale_kodu,
    t.name as ihale_adi,
    tl.id as tender_line_id,
    tl.sequence as line_sequence,
    
    -- ÜRÜN BİLGİLERİ / PRODUCT INFO
    pp.id as product_id,
    pp.default_code as product_code,
    COALESCE((pt.name::jsonb)->>'tr_TR', (pt.name::jsonb)->>'en_US', pt.name::text) as product_name,
    pc.complete_name as product_category,
    tl.quantity as miktar,
    COALESCE((uom.name::jsonb)->>'tr_TR', (uom.name::jsonb)->>'en_US', uom.name::text) as birim,
    
    -- SATINALMACI BİLGİLERİ / BUYER INFO
    t.buyer_id,
    COALESCE(buyer_partner.name, 'Atanmamış') as satinalmaci_adi,
    buyer_user.login as satinalmaci_email,
    
    -- TARİH BİLGİLERİ / DATE INFO (Filtreleme için)
    t.start_date as ihale_baslangic,
    t.end_date as ihale_bitis,
    t.workflow_end_date as tamamlanma_tarihi,
    EXTRACT(YEAR FROM t.start_date) as yil,
    EXTRACT(MONTH FROM t.start_date) as ay,
    EXTRACT(QUARTER FROM t.start_date) as ceyrek,
    TO_CHAR(t.start_date, 'YYYY-MM') as yil_ay,
    TO_CHAR(t.start_date, 'YYYY-Q') as yil_ceyrek,
    
    -- FİNANSAL METRIKLER (ÜRÜN BAZLI) / FINANCIAL METRICS (PER PRODUCT)
    -- Hedef Fiyat (Target Price)
    tl.target_price,
    tl.target_price * (1 - tl.target_discount) * tl.quantity as hedef_fiyat_toplam,
    
    -- İlk Turda Bu Ürün İçin Verilen En Düşük Teklif
    COALESCE((
        SELECT MIN(pol.price_unit * (1 - tl.target_discount))
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = 1
        AND pol.price_unit > 0
    ), 0) as ilk_tur_en_dusuk_fiyat,
    
    COALESCE((
        SELECT MIN(pol.price_unit * (1 - tl.target_discount)) * tl.quantity
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = 1
        AND pol.price_unit > 0
    ), 0) as ilk_tur_en_dusuk_fiyat_toplam,
    
    -- Mevcut Turdaki En Düşük Teklif (Current Round Lowest Bid) - Bu ürün için
    COALESCE((
        SELECT MIN(pol.price_unit * (1 - tl.target_discount))
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = t.tender_round
        AND pol.price_unit > 0
    ), 0) as mevcut_tur_en_dusuk_fiyat,
    
    COALESCE((
        SELECT MIN(pol.price_unit * (1 - tl.target_discount)) * tl.quantity
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = t.tender_round
        AND pol.price_unit > 0
    ), 0) as mevcut_tur_en_dusuk_fiyat_toplam,
    
    -- Saving (İlk Tur En Düşük - Mevcut Tur En Düşük)
    COALESCE((
        SELECT MIN(pol.price_unit) * tl.quantity
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = 1
        AND pol.price_unit > 0
    ), 0) - COALESCE((
        SELECT MIN(pol.price_unit * (1 - tl.target_discount)) * tl.quantity
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = t.tender_round
        AND pol.price_unit > 0
    ), 0) as saving_tutar,
    
    -- Saving Yüzdesi (%)
    CASE
        WHEN COALESCE((
            SELECT MIN(pol.price_unit * (1 - tl.target_discount)) * tl.quantity
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = t.id
            AND pol.product_id = tl.product_id
            AND po.tender_round = 1
            AND pol.price_unit > 0
        ), 0) > 0 THEN
            ROUND((
                (COALESCE((
                    SELECT MIN(pol.price_unit * (1 - tl.target_discount)) * tl.quantity
                    FROM purchase_order po
                    JOIN purchase_order_line pol ON pol.order_id = po.id
                    WHERE po.tender_id = t.id
                    AND pol.product_id = tl.product_id
                    AND po.tender_round = 1
                    AND pol.price_unit > 0
                ), 0) - COALESCE((
                    SELECT MIN(pol.price_unit * (1 - tl.target_discount)) * tl.quantity
                    FROM purchase_order po
                    JOIN purchase_order_line pol ON pol.order_id = po.id
                    WHERE po.tender_id = t.id
                    AND pol.product_id = tl.product_id
                    AND po.tender_round = t.tender_round
                    AND pol.price_unit > 0
                ), 0)) /
                COALESCE((
                    SELECT MIN(pol.price_unit * (1 - tl.target_discount)) * tl.quantity
                    FROM purchase_order po
                    JOIN purchase_order_line pol ON pol.order_id = po.id
                    WHERE po.tender_id = t.id
                    AND pol.product_id = tl.product_id
                    AND po.tender_round = 1
                    AND pol.price_unit > 0
                ), 1) * 100
            )::numeric, 2)
        ELSE 0
    END as saving_yuzdesi,
    
    -- Hedef Fiyata Yakınlık Oranı (Mevcut Tur En Düşük / Hedef * 100)
    CASE
        WHEN tl.target_price > 0 THEN
            ROUND((
                COALESCE((
                    SELECT MIN(pol.price_unit * (1 - tl.target_discount))
                    FROM purchase_order po
                    JOIN purchase_order_line pol ON pol.order_id = po.id
                    WHERE po.tender_id = t.id
                    AND pol.product_id = tl.product_id
                    AND po.tender_round = t.tender_round
                    AND pol.price_unit > 0
                ), 0) / tl.target_price * 100
            )::numeric, 0)
        ELSE 0
    END as yakinlik_orani_yuzde,
    
    -- TEDARİKÇİ METRIKLERI (BU ÜRÜN İÇİN) / SUPPLIER METRICS (FOR THIS PRODUCT)
    -- Bu ürün için teklif veren tedarikçi sayısı
    (
        SELECT COUNT(DISTINCT po.partner_id)
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND pol.price_unit > 0
    ) as tedarikci_sayisi,
    
    -- Mevcut turda en düşük teklifi veren tedarikçi (bu ürün için)
    (
        SELECT partner.name
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        JOIN res_partner partner ON po.partner_id = partner.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = t.tender_round
        AND pol.price_unit > 0
        ORDER BY pol.price_unit * (1 - pol.discount)   ASC
        LIMIT 1
    ) as en_dusuk_teklif_veren_tedarikci,
    
    -- Bu tedarikçi yeni mi? (eğer kazanan olursa)
    (
        SELECT CASE WHEN NOT EXISTS (
            SELECT 1 FROM purchase_order po2
            WHERE po2.partner_id = po.partner_id
            AND po2.id < po.id
            AND po2.state IN ('purchase', 'done')
        ) THEN 1 ELSE 0 END
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = t.tender_round
        AND pol.price_unit > 0
        ORDER BY pol.price_unit ASC
        LIMIT 1
    ) as yeni_tedarikci_mi,
    
    -- VADE VE NPV (BU ÜRÜN İÇİN) / PAYMENT TERMS & NPV (FOR THIS PRODUCT)
    -- Vade (gün) - mevcut turdaki en düşük teklifin vade bilgisi
    COALESCE((
        SELECT MAX(COALESCE(ptl.nb_days, 0))
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        LEFT JOIN account_payment_term pt ON po.payment_term_id = pt.id
        LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = t.tender_round
        AND pol.price_unit > 0
    ), 0) as vade_gun,
    
    -- NPV Kazancı (bu ürün için - mevcut tur en düşük teklif bazlı)
    ROUND(COALESCE((
        SELECT (MIN(pol.price_unit) * tl.quantity) *
            COALESCE(MAX(ptl.nb_days), 0) / 365.0 * 0.25
        FROM purchase_order po
        JOIN purchase_order_line pol ON pol.order_id = po.id
        LEFT JOIN account_payment_term pt ON po.payment_term_id = pt.id
        LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt.id
        WHERE po.tender_id = t.id
        AND pol.product_id = tl.product_id
        AND po.tender_round = t.tender_round
        AND pol.price_unit > 0
    ), 0)::numeric, 2) as npv_kazanci,
    
    -- ZAMAN VE SLA METRIKLERI / TIME & SLA METRICS
    -- Zamanında mı tamamlandı?
    CASE
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_end_date <= t.end_date THEN 'E'
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_end_date > t.end_date THEN 'G'
        WHEN t.workflow_end_date IS NULL AND NOW() <= t.end_date THEN 'D' -- Devam Ediyor
        ELSE 'G'
    END as zamaninda_tamamlandi,
    
    -- Tamamlanma süresi (gün)
    CASE
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_start_date IS NOT NULL THEN
            DATE_PART('day', t.workflow_end_date - t.workflow_start_date)::integer
        ELSE NULL
    END as tamamlanma_suresi_gun,
    
    -- SLA gecikme süresi (dakika) - negatifse erken, pozitifse geç
    CASE
        WHEN t.workflow_end_date IS NOT NULL THEN
            DATE_PART('epoch', t.workflow_end_date - t.end_date)::integer / 60
        ELSE NULL
    END as sla_gecikme_dakika,
    
    -- DURUM BİLGİLERİ / STATUS INFO
    t.tender_type,
    CASE
        WHEN t.tender_type = 'direct' THEN 'Direkt'
        WHEN t.tender_type = 'indirect' THEN 'Endirekt'
        WHEN t.tender_type = 'mice' THEN 'MICE'
        WHEN t.tender_type = 'promotion' THEN 'Promosyon'
        ELSE t.tender_type
    END as ihale_tipi_label,
    
    COALESCE((ws.name::jsonb)->>'tr_TR', ws.name::text) as workflow_durumu,
    ws.code as workflow_durum_kodu,
    
    -- Para birimi
    curr.name as para_birimi,
    curr.symbol as para_birimi_sembol,
    
    -- DİĞER BİLGİLER / OTHER INFO
    t.is_urgent as acil_mi,
    t.country_id,
    country.name as ulke,
    t.city as sehir,
    
    -- Line Para Birimi / Line Currency
    tl.currency_id as line_currency_id,
    line_curr.name as line_para_birimi,
    line_curr.symbol as line_para_birimi_sembol,
    
    -- Hedef Tipi ve İskonto / Target Type and Discount
    tl.target_type as line_target_type,
    CASE
        WHEN tl.target_type = 'price' THEN 'Fiyat'
        WHEN tl.target_type = 'discount' THEN 'İndirim'
        ELSE tl.target_type
    END as line_target_type_label,
    tl.target_discount as line_target_discount

FROM ak_tender t
    -- Tender Lines (Her satır bir ürün)
    INNER JOIN ak_tender_line tl ON tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)
    
    -- Product Information
    LEFT JOIN product_product pp ON tl.product_id = pp.id
    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
    LEFT JOIN product_category pc ON pt.categ_id = pc.id
    LEFT JOIN uom_uom uom ON tl.uom_id = uom.id
    
    -- Buyer
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
    
    -- Workflow
    LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
    
    -- Currency & Country
    LEFT JOIN res_currency curr ON t.currency_id = curr.id
    LEFT JOIN res_currency line_curr ON tl.currency_id = line_curr.id
    LEFT JOIN res_country country ON t.country_id = country.id

ORDER BY t.start_date DESC, t.id DESC, tl.sequence;


DROP VIEW IF EXISTS view_buyer_monthly_trend CASCADE;

CREATE VIEW view_buyer_monthly_trend AS
-- ============================================================================
-- AYLIK TREND DATASET: Satınalmacı Bazında Aylık Toplu Veriler
-- ============================================================================
-- Zaman serisi grafikleri için. Her satır bir satınalmacının bir ayı.

SELECT
    -- Satınalmacı
    buyer_user.id as buyer_id,
    COALESCE(buyer_partner.name, 'Atanmamış') as satinalmaci_adi,
    
    -- Zaman
    EXTRACT(YEAR FROM t.start_date) as yil,
    EXTRACT(MONTH FROM t.start_date) as ay,
    TO_CHAR(t.start_date, 'YYYY-MM') as yil_ay,
    TO_CHAR(t.start_date, 'Mon YYYY') as ay_label,
    EXTRACT(QUARTER FROM t.start_date) as ceyrek,
    
    -- İhale Sayıları
    COUNT(DISTINCT t.id) as ihale_sayisi,
    COUNT(DISTINCT CASE WHEN t.workflow_end_date IS NOT NULL THEN t.id END) as tamamlanan_ihale_sayisi,
    
    -- Ortalama Saving % (İlk tur en düşük fiyat bazlı)
    AVG(
        CASE
            WHEN (
                SELECT SUM(first_round.min_price * first_round.qty)
                FROM (
                    SELECT
                        pol.product_id,
                        MIN(pol.price_unit) as min_price,
                        MAX(pol.product_qty) as qty
                    FROM purchase_order po
                    JOIN purchase_order_line pol ON pol.order_id = po.id
                    WHERE po.tender_id = t.id
                    AND po.tender_round = 1
                    AND pol.price_unit > 0
                    GROUP BY pol.product_id
                ) first_round
            ) > 0 THEN
                (
                    (SELECT SUM(first_round.min_price * first_round.qty)
                     FROM (
                         SELECT
                             pol.product_id,
                             MIN(pol.price_unit) as min_price,
                             MAX(pol.product_qty) as qty
                         FROM purchase_order po
                         JOIN purchase_order_line pol ON pol.order_id = po.id
                         WHERE po.tender_id = t.id
                         AND po.tender_round = 1
                         AND pol.price_unit > 0
                         GROUP BY pol.product_id
                     ) first_round) -
                    (SELECT COALESCE(SUM(pol.price_unit * pol.product_qty), 0)
                     FROM purchase_order po
                     JOIN purchase_order_line pol ON pol.order_id = po.id
                     WHERE po.tender_id = t.id
                     AND po.state IN ('purchase', 'done'))
                ) /
                (SELECT SUM(first_round.min_price * first_round.qty)
                 FROM (
                     SELECT
                         pol.product_id,
                         MIN(pol.price_unit) as min_price,
                         MAX(pol.product_qty) as qty
                     FROM purchase_order po
                     JOIN purchase_order_line pol ON pol.order_id = po.id
                     WHERE po.tender_id = t.id
                     AND po.tender_round = 1
                     AND pol.price_unit > 0
                     GROUP BY pol.product_id
                 ) first_round) * 100
            ELSE 0
        END
    )::numeric(10,2) as ortalama_saving_yuzde,
    
    -- Toplam Saving
    SUM(
        COALESCE((
            SELECT SUM(first_round.min_price * first_round.qty)
            FROM (
                SELECT
                    pol.product_id,
                    MIN(pol.price_unit) as min_price,
                    MAX(pol.product_qty) as qty
                FROM purchase_order po
                JOIN purchase_order_line pol ON pol.order_id = po.id
                WHERE po.tender_id = t.id
                AND po.tender_round = 1
                AND pol.price_unit > 0
                GROUP BY pol.product_id
            ) first_round
        ), 0) - COALESCE((
            SELECT SUM(pol.price_unit * pol.product_qty)
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            WHERE po.tender_id = t.id
            AND po.state IN ('purchase', 'done')
        ), 0)
    ) as toplam_saving,
    
    -- Ortalama Tedarikçi Sayısı
    AVG(
        (SELECT COUNT(DISTINCT po.partner_id)
         FROM purchase_order po
         WHERE po.tender_id = t.id)
    )::numeric(10,2) as ortalama_tedarikci_sayisi,
    
    -- Toplam Yeni Tedarikçi
    SUM(
        (SELECT COUNT(DISTINCT po.partner_id)
         FROM purchase_order po
         WHERE po.tender_id = t.id
         AND po.state IN ('purchase', 'done')
         AND NOT EXISTS (
             SELECT 1 FROM purchase_order po2
             WHERE po2.partner_id = po.partner_id
             AND po2.id < po.id
             AND po2.state IN ('purchase', 'done')
         ))
    ) as yeni_tedarikci_toplam,
    
    -- Zamanında Tamamlanma Oranı %
    CASE
        WHEN COUNT(DISTINCT CASE WHEN t.workflow_end_date IS NOT NULL THEN t.id END) > 0 THEN
            ROUND((
                COUNT(DISTINCT CASE
                    WHEN t.workflow_end_date IS NOT NULL
                    AND t.workflow_end_date <= t.end_date
                    THEN t.id
                END)::numeric /
                COUNT(DISTINCT CASE WHEN t.workflow_end_date IS NOT NULL THEN t.id END)::numeric * 100
            ), 2)
        ELSE 0
    END as zamaninda_tamamlama_orani,
    
    -- Toplam NPV
    SUM(
        ROUND(COALESCE((
            SELECT SUM(
                (pol.price_unit * pol.product_qty) *
                COALESCE(ptl.nb_days, 0) / 365.0 * 0.25
            )
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            LEFT JOIN account_payment_term pt ON po.payment_term_id = pt.id
            LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt.id
            WHERE po.tender_id = t.id
            AND po.state IN ('purchase', 'done')
            AND pol.price_unit > 0
        ), 0)::numeric, 2)
    ) as toplam_npv

FROM ak_tender t
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id

WHERE t.buyer_id IS NOT NULL

GROUP BY
    buyer_user.id,
    buyer_partner.name,
    EXTRACT(YEAR FROM t.start_date),
    EXTRACT(MONTH FROM t.start_date),
    TO_CHAR(t.start_date, 'YYYY-MM'),
    TO_CHAR(t.start_date, 'Mon YYYY'),
    EXTRACT(QUARTER FROM t.start_date)

ORDER BY yil DESC, ay DESC, satinalmaci_adi;


DROP VIEW IF EXISTS view_buyer_performance_summary CASCADE;

CREATE VIEW view_buyer_performance_summary AS
-- ============================================================================
-- 7. SATINALMACI PERFORMANS ÖZET RAPORU (BUYER PERFORMANCE SUMMARY REPORT)
-- ============================================================================
-- Satınalmacıların performans metriklerini hesaplar
-- Calculates buyer performance metrics for dashboard

SELECT
    -- Satınalmacı Bilgileri / Buyer Information
    buyer_user.id as buyer_id,
    buyer_partner.name as buyer_name,
    buyer_user.login as buyer_email,
    
    -- Zaman Filtresi / Time Period
    EXTRACT(YEAR FROM t.start_date) as year,
    EXTRACT(MONTH FROM t.start_date) as month,
    TO_CHAR(t.start_date, 'YYYY-MM') as year_month,
    
    -- İhale Sayıları / Tender Counts
    COUNT(DISTINCT t.id) as total_tenders,
    COUNT(DISTINCT CASE WHEN t.tender_type = 'direct' THEN t.id END) as direct_tenders,
    COUNT(DISTINCT CASE WHEN t.tender_type = 'indirect' THEN t.id END) as indirect_tenders,
    COUNT(DISTINCT CASE WHEN t.tender_type = 'mice' THEN t.id END) as mice_tenders,
    
    -- Toplam Saving (Kazanç) Hesaplama / Total Saving Calculation
    -- Hedef fiyat ile kazanılan fiyat arasındaki fark
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            ((tl.target_price * tl.quantity) - (pol.price_unit * pol.product_qty))
        ELSE 0
    END) as total_saving_amount,
    
    -- Toplam Hedef Fiyat / Total Target Price
    SUM(tl.target_price * tl.quantity) as total_target_value,
    
    -- Toplam Kazanılan Fiyat / Total Won Price
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            (pol.price_unit * pol.product_qty)
        ELSE 0
    END) as total_won_value,
    
    -- Saving Yüzdesi / Saving Percentage
    CASE
        WHEN SUM(tl.target_price * tl.quantity) > 0 THEN
            ROUND(((SUM(CASE
                WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
                    ((tl.target_price * tl.quantity) - (pol.price_unit * pol.product_qty))
                ELSE 0
            END) / SUM(tl.target_price * tl.quantity)) * 100)::numeric, 2)
        ELSE 0
    END as total_saving_percentage,
    
    -- Hedef Fiyata Yakınlık Oranı / Target Price Proximity Rate
    -- 100 - saving % = yakınlık oranı (100% hedef, ne kadar yakınsa o kadar iyi)
    CASE
        WHEN SUM(tl.target_price * tl.quantity) > 0 THEN
            ROUND((100 - (SUM(CASE
                WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
                    ((tl.target_price * tl.quantity) - (pol.price_unit * pol.product_qty))
                ELSE 0
            END) / SUM(tl.target_price * tl.quantity) * 100))::numeric, 2)
        ELSE 0
    END as target_proximity_rate,
    
    -- NPV (Net Present Value) Kazancı / NPV Gain
    -- Vade farkından kaynaklanan kazanç hesabı
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND po.payment_term_id IS NOT NULL AND pol.price_unit > 0 THEN
            -- Basitleştirilmiş NPV hesabı: tutar * (vade günü / 365) * faiz oranı
            (pol.price_unit * pol.product_qty *
             COALESCE(ptl.nb_days, 30) / 365.0 * 0.25)
        ELSE 0
    END) as npv_gain_estimated,
    
    -- Ortalama Vade / Average Payment Term
    AVG(CASE
        WHEN po.state IN ('purchase', 'done') AND po.payment_term_id IS NOT NULL AND pol.price_unit > 0 THEN
            COALESCE(ptl.nb_days, 30)
        ELSE NULL
    END) as avg_payment_term_days,
    
    -- Tedarikçi Sayıları / Supplier Counts
    COUNT(DISTINCT CASE
        WHEN po.state IN ('draft', 'sent', 'purchase', 'done') THEN po.partner_id
    END) as total_suppliers_participated,
    
    -- Benzersiz tedarikçi sayısı (ilk defa çalışılan)
    COUNT(DISTINCT CASE
        WHEN po.state IN ('purchase', 'done')
        AND NOT EXISTS (
            SELECT 1 FROM purchase_order po2
            WHERE po2.partner_id = po.partner_id
            AND po2.id < po.id
            AND po2.state IN ('purchase', 'done')
        ) THEN po.partner_id
    END) as new_suppliers_count,
    
    -- Zamanında Tamamlanan İhale Sayısı / On-time Completed Tenders
    COUNT(DISTINCT CASE
        WHEN t.workflow_end_date IS NOT NULL
        AND t.workflow_end_date <= t.end_date
        THEN t.id
    END) as on_time_tenders,
    
    -- Zamanında Tamamlama Oranı / On-time Completion Rate
    CASE
        WHEN COUNT(DISTINCT CASE WHEN t.workflow_end_date IS NOT NULL THEN t.id END) > 0 THEN
            ROUND((COUNT(DISTINCT CASE
                WHEN t.workflow_end_date IS NOT NULL
                AND t.workflow_end_date <= t.end_date
                THEN t.id
            END)::numeric /
            COUNT(DISTINCT CASE WHEN t.workflow_end_date IS NOT NULL THEN t.id END)::numeric * 100), 2)
        ELSE 0
    END as on_time_completion_rate,
    
    -- Ortalama İhale Tamamlanma Süresi (gün) / Average Tender Completion Time
    AVG(CASE
        WHEN t.workflow_end_date IS NOT NULL THEN
            DATE_PART('day', t.workflow_end_date - t.workflow_start_date)
    END) as avg_completion_days,
    
    -- SLA İhlal Sayısı / SLA Violation Count
    COUNT(DISTINCT CASE
        WHEN t.workflow_end_date IS NOT NULL
        AND t.workflow_end_date > t.end_date
        THEN t.id
    END) as sla_violated_tenders

FROM ak_tender t
    -- Buyer Information
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
    
    -- Tender Lines
    LEFT JOIN ak_tender_line tl ON tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)
    
    -- Purchase Orders (Teklifler)
    LEFT JOIN purchase_order po ON po.tender_id = t.id
    
    -- Purchase Order Lines
    LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
        AND pol.product_id = tl.product_id
    
    -- Payment Terms
    LEFT JOIN account_payment_term pt ON po.payment_term_id = pt.id
    LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt.id

WHERE t.buyer_id IS NOT NULL

GROUP BY
    buyer_user.id,
    buyer_partner.name,
    buyer_user.login,
    EXTRACT(YEAR FROM t.start_date),
    EXTRACT(MONTH FROM t.start_date),
    TO_CHAR(t.start_date, 'YYYY-MM')

ORDER BY year DESC, month DESC, buyer_name;


DROP VIEW IF EXISTS view_buyer_tender_detail CASCADE;

CREATE VIEW view_buyer_tender_detail AS
-- ============================================================================
-- 8. SATINALMACI İHALE DETAY RAPORU (BUYER TENDER DETAIL REPORT)
-- ============================================================================
-- Dashboard alt tablosu için ihale bazlı detaylar
-- Tender-level details for dashboard bottom table

SELECT
    -- İhale Bilgileri / Tender Information
    t.id as tender_id,
    t.code as tender_code,
    t.name as tender_name,
    t.start_date,
    t.end_date,
    
    -- Satınalmacı / Buyer
    buyer_user.id as buyer_id,
    buyer_partner.name as buyer_name,
    
    -- Hedef Fiyat / Target Price
    SUM(tl.target_price * tl.quantity) as target_price_total,
    
    -- Kazanılan Fiyat / Won Price
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            (pol.price_unit * pol.product_qty)
        ELSE 0
    END) as won_price_total,
    
    -- Yakınlık Oranı % / Proximity Rate %
    CASE
        WHEN SUM(tl.target_price * tl.quantity) > 0 THEN
            ROUND(((SUM(CASE
                WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
                    (pol.price_unit * pol.product_qty)
                ELSE 0
            END) / SUM(tl.target_price * tl.quantity)) * 100)::numeric, 2)
        ELSE 0
    END as proximity_rate_percentage,
    
    -- Vade (Gün) / Payment Term (Days)
    MAX(CASE
        WHEN po.state IN ('purchase', 'done') AND po.payment_term_id IS NOT NULL AND pol.price_unit > 0 THEN
            COALESCE(ptl.nb_days, 0)
        ELSE 0
    END) as payment_term_days,
    
    -- NPV Kazancı / NPV Gain
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND po.payment_term_id IS NOT NULL AND pol.price_unit > 0 THEN
            (pol.price_unit * pol.product_qty *
             COALESCE(ptl.nb_days, 30) / 365.0 * 0.25)
        ELSE 0
    END) as npv_gain,
    
    -- On-time Durumu / On-time Status
    CASE
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_end_date <= t.end_date THEN 'E'
        WHEN t.workflow_end_date IS NOT NULL AND t.workflow_end_date > t.end_date THEN 'G'
        WHEN t.workflow_end_date IS NULL AND NOW() <= t.end_date THEN 'D'
        ELSE 'G'
    END as on_time_status,
    
    -- Saving Tutarı / Saving Amount
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            ((tl.target_price * tl.quantity) - (pol.price_unit * pol.product_qty))
        ELSE 0
    END) as saving_amount,
    
    -- Saving Yüzdesi / Saving Percentage
    CASE
        WHEN SUM(tl.target_price * tl.quantity) > 0 THEN
            ROUND(((SUM(CASE
                WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
                    ((tl.target_price * tl.quantity) - (pol.price_unit * pol.product_qty))
                ELSE 0
            END) / SUM(tl.target_price * tl.quantity)) * 100)::numeric, 2)
        ELSE 0
    END as saving_percentage,
    
    -- Tedarikçi Sayısı / Supplier Count
    COUNT(DISTINCT po.partner_id) as supplier_count,
    
    -- İhale Durumu / Tender Status
    COALESCE((ws.name::jsonb)->>'tr_TR', (ws.name::jsonb)->>'en_US', ws.name::text) as workflow_state,
    
    -- Para Birimi / Currency
    curr.name as currency,
    curr.symbol as currency_symbol,
    
    -- Tamamlanma Tarihi / Completion Date
    t.workflow_end_date,
    
    -- Zaman Analizi / Time Analysis
    EXTRACT(YEAR FROM t.start_date) as year,
    EXTRACT(MONTH FROM t.start_date) as month,
    TO_CHAR(t.start_date, 'YYYY-MM') as year_month

FROM ak_tender t
    -- Buyer
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
    
    -- Workflow State
    LEFT JOIN ak_workflow_state ws ON t.workflow_current_state_id = ws.id
    
    -- Currency
    LEFT JOIN res_currency curr ON t.currency_id = curr.id
    
    -- Tender Lines
    LEFT JOIN ak_tender_line tl ON tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)
    
    -- Purchase Orders
    LEFT JOIN purchase_order po ON po.tender_id = t.id
    
    -- Purchase Order Lines
    LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
        AND pol.product_id = tl.product_id
    
    -- Payment Terms
    LEFT JOIN account_payment_term pt ON po.payment_term_id = pt.id
    LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt.id

WHERE t.buyer_id IS NOT NULL

GROUP BY
    t.id, t.code, t.name, t.start_date, t.end_date, t.workflow_end_date,
    buyer_user.id, buyer_partner.name,
    ws.name, curr.name, curr.symbol

ORDER BY t.start_date DESC;


DROP VIEW IF EXISTS view_buyer_supplier_statistics CASCADE;

CREATE VIEW view_buyer_supplier_statistics AS
-- ============================================================================
-- 9. SATINALMACI TEDARİKÇİ İSTATİSTİKLERİ (BUYER SUPPLIER STATISTICS)
-- ============================================================================
-- Satınalmacı bazında tedarikçi istatistikleri
-- Supplier statistics by buyer for charts

SELECT
    -- Satınalmacı / Buyer
    buyer_user.id as buyer_id,
    buyer_partner.name as buyer_name,
    
    -- Zaman / Time Period
    EXTRACT(YEAR FROM po.date_order) as year,
    EXTRACT(MONTH FROM po.date_order) as month,
    TO_CHAR(po.date_order, 'YYYY-MM') as year_month,
    EXTRACT(QUARTER FROM po.date_order) as quarter,
    
    -- İhale Başına Tedarikçi Sayısı / Suppliers per Tender
    t.id as tender_id,
    t.code as tender_code,
    COUNT(DISTINCT po.partner_id) as suppliers_per_tender,
    
    -- Yeni Tedarikçi mi? / Is New Supplier?
    COUNT(DISTINCT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM purchase_order po2
            WHERE po2.partner_id = po.partner_id
            AND po2.id < po.id
            AND po2.state IN ('purchase', 'done')
        ) THEN po.partner_id
    END) as new_suppliers_in_tender,
    
    -- Toplam Teklif Veren Tedarikçi / Total Bidding Suppliers
    COUNT(DISTINCT po.partner_id) as total_suppliers,
    
    -- Kazanan Tedarikçi Sayısı / Winning Suppliers
    COUNT(DISTINCT CASE
        WHEN po.state IN ('purchase', 'done') THEN po.partner_id
    END) as winning_suppliers

FROM ak_tender t
    -- Purchase Orders
    INNER JOIN purchase_order po ON po.tender_id = t.id
    
    -- Buyer
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id

WHERE t.buyer_id IS NOT NULL

GROUP BY
    buyer_user.id,
    buyer_partner.name,
    EXTRACT(YEAR FROM po.date_order),
    EXTRACT(MONTH FROM po.date_order),
    TO_CHAR(po.date_order, 'YYYY-MM'),
    EXTRACT(QUARTER FROM po.date_order),
    t.id,
    t.code

ORDER BY year DESC, month DESC, tender_id;


DROP VIEW IF EXISTS view_buyer_monthly_aggregates CASCADE;

CREATE VIEW view_buyer_monthly_aggregates AS
-- ============================================================================
-- 10. SATINALMACI AYLIK TOPLAM VERİLER (BUYER MONTHLY AGGREGATES)
-- ============================================================================
-- Dashboard grafikleri için aylık toplu veriler
-- Monthly aggregate data for dashboard charts

SELECT
    -- Satınalmacı / Buyer
    buyer_user.id as buyer_id,
    buyer_partner.name as buyer_name,
    buyer_user.login as buyer_email,
    
    -- Zaman Dilimleri / Time Periods
    EXTRACT(YEAR FROM t.start_date) as year,
    EXTRACT(MONTH FROM t.start_date) as month,
    TO_CHAR(t.start_date, 'YYYY-MM') as year_month,
    EXTRACT(QUARTER FROM t.start_date) as quarter,
    TO_CHAR(t.start_date, 'Mon') as month_name,
    
    -- İhale Sayıları / Tender Counts
    COUNT(DISTINCT t.id) as tender_count,
    
    -- Toplam Tasarruf / Total Savings
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            ((tl.target_price * tl.quantity) - (pol.price_unit * pol.product_qty))
        ELSE 0
    END) as total_saving,
    
    -- Toplam Saving Yüzdesi (Aylık Ortalama) / Average Saving Percentage
    AVG(CASE
        WHEN tl.target_price > 0 AND po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            (((tl.target_price - pol.price_unit) / tl.target_price) * 100)
        ELSE 0
    END) as avg_saving_percentage,
    
    -- Toplam Hedef Fiyat / Total Target Price
    SUM(tl.target_price * tl.quantity) as total_target_price,
    
    -- Toplam Kazanılan Fiyat / Total Won Price
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            (pol.price_unit * pol.product_qty)
        ELSE 0
    END) as total_won_price,
    
    -- Ortalama Yakınlık Oranı / Average Proximity Rate
    AVG(CASE
        WHEN tl.target_price > 0 AND po.state IN ('purchase', 'done') AND pol.price_unit > 0 THEN
            ((pol.price_unit / tl.target_price) * 100)
        ELSE 0
    END) as avg_proximity_rate,
    
    -- Toplam NPV Kazancı / Total NPV Gain
    SUM(CASE
        WHEN po.state IN ('purchase', 'done') AND po.payment_term_id IS NOT NULL AND pol.price_unit > 0 THEN
            (pol.price_unit * pol.product_qty *
             COALESCE(ptl.nb_days, 30) / 365.0 * 0.25)
        ELSE 0
    END) as total_npv_gain,
    
    -- Ortalama Tedarikçi Sayısı / Average Suppliers per Tender
    AVG(supplier_counts.supplier_count) as avg_suppliers_per_tender,
    
    -- Yeni Tedarikçi Sayısı / New Suppliers Count
    COUNT(DISTINCT CASE
        WHEN po.state IN ('purchase', 'done')
        AND NOT EXISTS (
            SELECT 1 FROM purchase_order po2
            WHERE po2.partner_id = po.partner_id
            AND po2.date_order < po.date_order
            AND po2.state IN ('purchase', 'done')
            AND EXTRACT(YEAR FROM po2.date_order) < EXTRACT(YEAR FROM t.start_date)
            OR (EXTRACT(YEAR FROM po2.date_order) = EXTRACT(YEAR FROM t.start_date)
                AND EXTRACT(MONTH FROM po2.date_order) < EXTRACT(MONTH FROM t.start_date))
        ) THEN po.partner_id
    END) as new_suppliers_this_month,
    
    -- Zamanında Tamamlama / On-time Completion
    COUNT(DISTINCT CASE
        WHEN t.workflow_end_date IS NOT NULL
        AND t.workflow_end_date <= t.end_date
        THEN t.id
    END) as on_time_tenders,
    
    COUNT(DISTINCT CASE
        WHEN t.workflow_end_date IS NOT NULL
        THEN t.id
    END) as completed_tenders,
    
    -- Zamanında Oran / On-time Rate
    CASE
        WHEN COUNT(DISTINCT CASE WHEN t.workflow_end_date IS NOT NULL THEN t.id END) > 0 THEN
            ROUND((COUNT(DISTINCT CASE
                WHEN t.workflow_end_date IS NOT NULL
                AND t.workflow_end_date <= t.end_date
                THEN t.id
            END)::numeric /
            COUNT(DISTINCT CASE WHEN t.workflow_end_date IS NOT NULL THEN t.id END)::numeric * 100), 2)
        ELSE 0
    END as on_time_rate

FROM ak_tender t
    -- Buyer
    LEFT JOIN res_users buyer_user ON t.buyer_id = buyer_user.id
    LEFT JOIN res_partner buyer_partner ON buyer_user.partner_id = buyer_partner.id
    
    -- Tender Lines
    LEFT JOIN ak_tender_line tl ON tl.tender_id = t.id
        AND (tl.display_type = 'product' OR tl.display_type IS NULL)
    
    -- Purchase Orders
    LEFT JOIN purchase_order po ON po.tender_id = t.id
    
    -- Purchase Order Lines
    LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
        AND pol.product_id = tl.product_id
    
    -- Payment Terms
    LEFT JOIN account_payment_term pt ON po.payment_term_id = pt.id
    LEFT JOIN account_payment_term_line ptl ON ptl.payment_id = pt.id
    
    -- Subquery for supplier counts per tender
    LEFT JOIN (
        SELECT
            tender_id,
            COUNT(DISTINCT partner_id) as supplier_count
        FROM purchase_order
        GROUP BY tender_id
    ) supplier_counts ON supplier_counts.tender_id = t.id

WHERE t.buyer_id IS NOT NULL

GROUP BY
    buyer_user.id,
    buyer_partner.name,
    buyer_user.login,
    EXTRACT(YEAR FROM t.start_date),
    EXTRACT(MONTH FROM t.start_date),
    TO_CHAR(t.start_date, 'YYYY-MM'),
    EXTRACT(QUARTER FROM t.start_date),
    TO_CHAR(t.start_date, 'Mon')

ORDER BY year DESC, month DESC, buyer_name;
