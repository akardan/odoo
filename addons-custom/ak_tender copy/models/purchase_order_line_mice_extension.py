# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    # ===== SENARYO İLİŞKİSİ =====
    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        compute='_compute_scenario_id',
        store=True,
        string='Senaryo'
    )
    
    scenario_date_id = fields.Many2one(
        'ak.tender.scenario.date',
        string='Seçilen Tarih',
        help='Tedarikçi hangi tarih seçeneğini seçti?'
    )
    
    # ===== PAKET FİYAT =====
    is_package_price = fields.Boolean(
        string='Paket Fiyat',
        help='Tedarikçi detay yerine paket fiyat verdi mi?'
    )
    
    # ===== NPV ALANLARI =====
    payment_term_days = fields.Integer(
        'Vade (Gün)',
        compute='_compute_payment_term_days',
        store=True,
        help='Ödeme vadesi gün sayısı'
    )
    
    price_npv = fields.Monetary(
        'NPV Fiyat',
        compute='_compute_price_npv',
        store=True,
        currency_field='currency_id',
        help='Net Bugünkü Değer bazlı fiyat'
    )
    
    npv_discount_amount = fields.Monetary(
        'NPV İskonto Tutarı',
        compute='_compute_price_npv',
        store=True,
        currency_field='currency_id',
        help='Vade farkından kaynaklanan iskonto'
    )
    
    @api.depends('tender_line_id.scenario_id')
    def _compute_scenario_id(self):
        for line in self:
            line.scenario_id = line.tender_line_id.scenario_id if line.tender_line_id else False
    
    @api.depends('order_id.payment_term_id')
    def _compute_payment_term_days(self):
        """Ödeme vadesi gün sayısını hesapla"""
        for line in self:
            if line.order_id.payment_term_id:
                # Payment term'den ortalama vade gününü hesapla
                terms = line.order_id.payment_term_id.line_ids
                if terms:
                    # Ağırlıklı ortalama hesapla - Odoo 18'de alan adı 'nb_days'
                    total_days = sum(term.nb_days * term.value_amount for term in terms)
                    line.payment_term_days = int(total_days / 100) if total_days else 0
                else:
                    line.payment_term_days = 0
            else:
                line.payment_term_days = 0  # Peşin ödeme
    
    @api.depends('price_unit', 'product_qty', 'payment_term_days', 'currency_id')
    def _compute_price_npv(self):
        """NPV bazlı fiyat hesapla"""
        for line in self:
            if line.payment_term_days > 0 and line.currency_id:
                # Gelecekteki toplam değer
                future_value = line.price_unit * line.product_qty
                
                # Mevcut economic data modelinden NPV oranını al
                # Varsayılan olarak %45 yıllık kullan
                npv_rate = 45.0  # Yıllık yüzde
                
                # Economic data varsa oradan al
                economic_data = self.env['ak.tender.economic.data'].search([
                    ('currency_id', '=', line.currency_id.id)
                ], limit=1)
                
                if economic_data and economic_data.npv_rate:
                    npv_rate = economic_data.npv_rate
                
                # NPV hesapla: PV = FV / (1 + r)^t
                # r = günlük oran, t = gün sayısı
                daily_rate = npv_rate / 100 / 365
                npv_value = future_value / ((1 + daily_rate) ** line.payment_term_days)
                
                line.price_npv = npv_value
                line.npv_discount_amount = future_value - npv_value
            else:
                # Peşin ödeme - NPV = nominal değer
                line.price_npv = line.price_unit * line.product_qty
                line.npv_discount_amount = 0.0
