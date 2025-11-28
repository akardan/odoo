# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # İhale (Tender) Settings - Genel Parametreler
    ak_tender_max_lead_time = fields.Integer(
        string=_('Maksimum Tedarik Süresi (Gün)'),
        config_parameter='ak_tender_max_lead_time',
        default=30,
        help=_("Direkt ihale tipinde izin verilen maksimum tedarik süresi (gün olarak).")
    )
    
    ak_tender_allow_alternative_products = fields.Boolean(
        string=_('Alternatif Ürünlere İzin Ver'),
        config_parameter='ak_tender_allow_alternative_products',
        default=True,
        help=_("Endirekt ihale tipinde alternatif ürün tekliflerine izin verilip verilmeyeceğini belirler.")
    )
    
    ak_tender_quality_approval_required = fields.Boolean(
        string=_('Kalite Onayı Gerekli'),
        config_parameter='ak_tender_quality_approval_required',
        default=True,
        help=_("Direkt ihale tipinde kalite onayının zorunlu olup olmadığını belirler.")
    )
    
    # İhale (Tender) Settings - NPV Hesaplama Parametreleri
    ak_tender_npv_interest_rate = fields.Float(
        string=_('NPV Faiz Oranı (%)'),
        config_parameter='ak_tender_npv_interest_rate',
        default=10.0,
        help=_("Net Bugünkü Değer (NPV) hesaplaması için varsayılan yıllık faiz oranı.")
    )
    
    # İhale (Tender) Settings - Hedef Fiyat Hesaplama Parametresi
    ak_tender_target_margin_below_lowest_offer = fields.Float(
        string=_('Hedef Marjı (%)'),
        config_parameter='ak_tender.target_margin_below_lowest_offer',
        default=15.0,
        help=_("En düşük teklifin ne kadar altında hedef fiyat/iskonto belirleneceğini ifade eder. Örneğin 15 değeri, en düşük teklifin %15 altı anlamına gelir.")
    )
    
    # Bulk Purchase Optimization Settings
    ak_tender_enable_bulk_purchase = fields.Boolean(
        string=_('Toplu Satın Alma Optimizasyonu'),
        config_parameter='ak_tender_enable_bulk_purchase',
        default=True,
        help=_("Toplu satın alma optimizasyonunu etkinleştirir.")
    )
    
    ak_tender_bulk_purchase_min_items = fields.Integer(
        string=_('Minimum Kalem Sayısı'),
        config_parameter='ak_tender_bulk_purchase_min_items',
        default=3,
        help=_("Toplu satın alma optimizasyonu için minimum kalem sayısı.")
    )
    
    ak_tender_bulk_purchase_min_value = fields.Float(
        string=_('Minimum Toplam Değer'),
        config_parameter='ak_tender_bulk_purchase_min_value',
        default=10000.0,
        help=_("Toplu satın alma optimizasyonu için minimum toplam değer.")
    )