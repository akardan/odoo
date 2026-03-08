-- View: public.view_dashboard_detail

-- DROP VIEW public.view_dashboard_detail;

CREATE OR REPLACE VIEW public.view_dashboard_detail
 AS
 SELECT t.id AS ihale_id,
    t.code AS ihale_kodu,
    t.name AS ihale_adi,
    tl.id AS tender_line_id,
    tl.sequence AS line_sira,
    pp.id AS product_id,
    pp.default_code AS product_kodu,
    COALESCE(pt.name ->> 'tr_TR'::text, pt.name ->> 'en_US'::text, pt.name::text) AS urun_adi,
    pc.complete_name AS urun_kategorisi,
    COALESCE(uom.name ->> 'tr_TR'::text, uom.name ->> 'en_US'::text, uom.name::text) AS birim,
    tl.quantity AS miktar,
    tl.days AS gun_sayisi,
    prl.material_group AS malzeme_grubu,
    prl.purchasing_group AS satin_alma_grubu,
    t.buyer_id,
    COALESCE(buyer_partner.name, 'Atanmamış'::character varying) AS satinalmaci_adi,
    buyer_user.login AS satinalmaci_email,
    t.start_date AS ihale_baslangic,
    t.end_date AS ihale_bitis,
    EXTRACT(year FROM t.end_date) AS yil,
    EXTRACT(month FROM t.end_date) AS ay,
    EXTRACT(week FROM t.end_date) AS hafta,
    to_char(t.end_date, 'YYYY-MM'::text) AS yil_ay,
    curr.name AS para_birimi,
    curr.symbol AS para_birimi_sembol,
    line_curr.name AS line_para_birimi,
    line_curr.symbol AS line_para_birimi_sembol,
    COALESCE(latest_rate.rate, 1.0) AS doviz_kuru_tl,
    to_char(latest_rate.name::timestamp with time zone, 'YYYY-MM-DD'::text) AS kur_tarihi,
    COALESCE(line_latest_rate.rate, 1.0) AS line_doviz_kuru_tl,
    to_char(line_latest_rate.name::timestamp with time zone, 'YYYY-MM-DD'::text) AS line_kur_tarihi,
    tl.target_price,
    tl.target_price * COALESCE(line_latest_rate.rate, 1.0) AS target_price_tl,
    tl.target_discount,
    tl.target_price::double precision * (1::double precision - tl.target_discount / 100::double precision) * tl.quantity AS target_total_untaxed,
    tl.target_price::double precision * (1::double precision - tl.target_discount / 100::double precision) * tl.quantity * COALESCE(line_latest_rate.rate, 1.0)::double precision AS target_total_untaxed_tl,
    COALESCE(( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0)) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0)) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) AS ilk_tur_birim_fiyat,
    COALESCE(( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0) *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0) *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) AS ilk_tur_birim_fiyat_tl,
    COALESCE(( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) AS ilk_tur_toplam_fiyat,
    COALESCE(( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) AS ilk_tur_toplam_fiyat_tl,
    COALESCE(( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0)) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0)) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0)) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0)) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric) AS mevcut_tur_birim_fiyat,
    COALESCE(( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0) *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0) *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0) *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0) *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric) AS mevcut_tur_birim_fiyat_tl,
    COALESCE(( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric), ( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric) AS mevcut_tur_toplam_fiyat,
    COALESCE(( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric), ( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric AND (EXISTS ( SELECT 1
                   FROM product_supplierinfo psi
                  WHERE psi.partner_id = po2.partner_id AND (psi.product_id = tl.product_id OR psi.product_tmpl_id = pp.product_tmpl_id) AND psi.is_approved = true))), ( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric) AS mevcut_tur_toplam_fiyat_tl,
    COALESCE(( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) - COALESCE(( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric), ( SELECT min(pol2.price_subtotal) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric) AS saving_tutar,
    COALESCE(( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) - COALESCE(( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric), ( SELECT min(pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END) AS min
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric) AS saving_tutar_tl,
        CASE
            WHEN COALESCE(( SELECT min(pol2.price_subtotal) AS min
               FROM purchase_order po2
                 JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
              WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) > 0::numeric THEN round((COALESCE(( SELECT min(pol2.price_subtotal) AS min
               FROM purchase_order po2
                 JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
              WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 0::numeric) - COALESCE(( SELECT min(pol2.price_subtotal) AS min
               FROM purchase_order po2
                 JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
              WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[])) AND pol2.price_unit > 0::numeric), ( SELECT min(pol2.price_subtotal) AS min
               FROM purchase_order po2
                 JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
              WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric)) / COALESCE(( SELECT min(pol2.price_subtotal) AS min
               FROM purchase_order po2
                 JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
              WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = 1 AND pol2.price_unit > 0::numeric), 1::numeric) * 100::numeric, 2)
            ELSE 0::numeric
        END AS saving_yuzdesi,
        CASE
            WHEN tl.target_price > 0::numeric THEN round(COALESCE(( SELECT min(pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0)) AS min
               FROM purchase_order po2
                 JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
              WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0::numeric) / tl.target_price * 100::numeric, 0)
            ELSE 0::numeric
        END AS yakinlik_orani_yuzde,
    ( SELECT count(DISTINCT po2.partner_id) AS count
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND pol2.price_unit > 0::numeric) AS tedarikci_sayisi,
    ( SELECT partner.name
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_partner partner ON po2.partner_id = partner.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric
          ORDER BY (pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0))
         LIMIT 1) AS en_dusuk_teklif_veren,
    COALESCE(( SELECT max(COALESCE(ptl2.nb_days, 0)) AS max
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             LEFT JOIN account_payment_term pt2 ON po2.payment_term_id = pt2.id
             LEFT JOIN account_payment_term_line ptl2 ON ptl2.payment_id = pt2.id
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric), 0) AS vade_gun,
    COALESCE(( SELECT pol2.price_subtotal - COALESCE(pol2.npv_value, 0::numeric) *
                CASE
                    WHEN npv_curr.name::text = po_curr.name::text THEN 1.0
                    ELSE COALESCE(cr_po.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_po ON true
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = pol2.tender_line_currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_npv ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[]))
          ORDER BY (pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0))
         LIMIT 1), ( SELECT pol2.price_subtotal - COALESCE(pol2.npv_value, 0::numeric) *
                CASE
                    WHEN npv_curr.name::text = po_curr.name::text THEN 1.0
                    ELSE COALESCE(cr_po.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_po ON true
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = pol2.tender_line_currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_npv ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric
          ORDER BY (pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0))
         LIMIT 1), 0::numeric) AS npv_kazanci,
    COALESCE(( SELECT pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_po.rate, 1.0)
                END - COALESCE(pol2.npv_value, 0::numeric) *
                CASE
                    WHEN npv_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_po ON true
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = pol2.tender_line_currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_npv ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND (po2.state::text = ANY (ARRAY['purchase'::character varying, 'done'::character varying]::text[]))
          ORDER BY (pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0))
         LIMIT 1), ( SELECT pol2.price_subtotal *
                CASE
                    WHEN po_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_po.rate, 1.0)
                END - COALESCE(pol2.npv_value, 0::numeric) *
                CASE
                    WHEN npv_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr_npv.rate, 1.0)
                END
           FROM purchase_order po2
             JOIN purchase_order_line pol2 ON pol2.order_id = po2.id
             JOIN res_currency po_curr ON po2.currency_id = po_curr.id
             LEFT JOIN res_currency npv_curr ON pol2.tender_line_currency_id = npv_curr.id
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = po2.currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_po ON true
             LEFT JOIN LATERAL ( SELECT res_currency_rate.rate
                   FROM res_currency_rate
                  WHERE res_currency_rate.currency_id = pol2.tender_line_currency_id AND (res_currency_rate.company_id = po2.company_id OR res_currency_rate.company_id IS NULL) AND res_currency_rate.name <= CURRENT_DATE
                  ORDER BY res_currency_rate.name DESC
                 LIMIT 1) cr_npv ON true
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(po2.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = po2.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE po2.tender_id = t.id AND pol2.product_id = tl.product_id AND po2.tender_round = t.tender_round AND pol2.price_unit > 0::numeric
          ORDER BY (pol2.price_unit * (1::numeric - COALESCE(pol2.discount, 0::numeric) / 100.0))
         LIMIT 1), 0::numeric) AS npv_kazanci_tl,
    COALESCE(ws.name ->> 'tr_TR'::text, ws.name::text) AS workflow_durumu,
    ws.code AS workflow_durum_kodu,
    t.tender_type,
        CASE
            WHEN t.tender_type::text = 'direct'::text THEN 'Direkt'::character varying
            WHEN t.tender_type::text = 'indirect'::text THEN 'Endirekt'::character varying
            WHEN t.tender_type::text = 'mice'::text THEN 'MICE'::character varying
            WHEN t.tender_type::text = 'promotion'::text THEN 'Promosyon'::character varying
            ELSE t.tender_type
        END AS ihale_tipi_label,
    t.is_urgent AS acil_mi,
    country.name AS ulke,
    t.city AS sehir,
    tl.required_delivery_date AS teslimat_tarihi,
    tl.lead_time_days AS temin_suresi_gun,
    tl.required AS gerekli_mi,
    tl.allow_alternative AS alternatif_kabul_mi
   FROM ak_tender t
     JOIN ak_tender_line tl ON tl.tender_id = t.id AND (tl.display_type::text = 'product'::text OR tl.display_type IS NULL)
     LEFT JOIN product_product pp ON tl.product_id = pp.id
     -- İhale tamamlanmış ise sadece siparişi dönüşmüş olan ürünler gelmeli
     LEFT JOIN ak_workflow_state ws_check ON t.workflow_current_state_id = ws_check.id
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
     LEFT JOIN LATERAL ( SELECT
                CASE
                    WHEN curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END AS rate,
            cr.name
           FROM res_currency_rate cr
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(t.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = t.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE cr.currency_id = t.currency_id AND (cr.company_id = t.company_id OR cr.company_id IS NULL) AND cr.name <= CURRENT_DATE
          ORDER BY cr.name DESC
         LIMIT 1) latest_rate ON true
     LEFT JOIN LATERAL ( SELECT
                CASE
                    WHEN line_curr.name::text = 'TRY'::text THEN 1.0
                    ELSE COALESCE(cr_try.rate, 1.0) / COALESCE(cr.rate, 1.0)
                END AS rate,
            cr.name
           FROM res_currency_rate cr
             LEFT JOIN LATERAL ( SELECT cr_t.rate
                   FROM res_currency_rate cr_t
                     JOIN res_company comp ON comp.id = COALESCE(t.company_id, 1)
                  WHERE cr_t.currency_id = comp.currency_id AND (cr_t.company_id = t.company_id OR cr_t.company_id IS NULL) AND cr_t.name <= CURRENT_DATE
                  ORDER BY cr_t.name DESC
                 LIMIT 1) cr_try ON true
          WHERE cr.currency_id = tl.currency_id AND (cr.company_id = t.company_id OR cr.company_id IS NULL) AND cr.name <= CURRENT_DATE
          ORDER BY cr.name DESC
         LIMIT 1) line_latest_rate ON true
  WHERE
    -- İhale tamamlanmış ise sadece siparişi dönüşmüş olan ürünler gelmeli
    (ws_check.code != 'completed' OR
     EXISTS (
       SELECT 1
       FROM purchase_order po_exists
       JOIN purchase_order_line pol_exists ON pol_exists.order_id = po_exists.id
       WHERE po_exists.tender_id = t.id
         AND pol_exists.product_id = tl.product_id
         AND po_exists.state IN ('purchase', 'done')
     ))
  ORDER BY t.end_date DESC, t.id DESC, tl.sequence;

ALTER TABLE public.view_dashboard_detail
    OWNER TO odoo;

