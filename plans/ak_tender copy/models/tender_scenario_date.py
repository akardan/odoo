# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AkTenderScenarioDate(models.Model):
    _name = 'ak.tender.scenario.date'
    _description = 'Senaryo Alternatif Tarihleri'
    _order = 'date_start'
    
    scenario_id = fields.Many2one('ak.tender.scenario', required=True, ondelete='cascade', string='Senaryo')
    
    name = fields.Char(string='Tarih Açıklaması', compute='_compute_name', store=True)
    # Örn: "2-4 Kasım 2025"
    
    date_start = fields.Date(string='Başlangıç', required=True)
    date_end = fields.Date(string='Bitiş', required=True)
    
    days = fields.Integer(compute='_compute_days', store=True, string='Gün Sayısı')
    
    sequence = fields.Integer(default=10, string='Sıra')
    
    is_preferred = fields.Boolean(
        string='Tercih Edilen Tarih',
        help='Bu tarih aralığı tercih edilen seçenektir'
    )
    
    notes = fields.Text(string='Notlar')
    
    # ===== MALİYET BOYUTU (KRİTİK!) =====
    # ⚠️ ÖNEMLİ: Tarih seçeneği senaryonun maliyet boyutudur!
    # Örn: 2-4 Kasım düşük sezon = 30,000€
    #      9-11 Kasım yüksek sezon = 35,000€
    
    currency_id = fields.Many2one(related='scenario_id.currency_id', string='Para Birimi')
    
    estimated_total_cost = fields.Monetary(
        string='Tahmini Toplam Maliyet',
        help='Bu tarih için beklenen toplam maliyet (sezon farkı, müsaitlik vb.)',
        currency_field='currency_id'
    )
    
    cost_multiplier = fields.Float(
        string='Maliyet Çarpanı',
        default=1.0,
        help='Sezon farkı çarpanı (1.0 = normal, 1.2 = %20 artış, 0.9 = %10 indirim)'
    )
    
    season_type = fields.Selection([
        ('low', 'Düşük Sezon'),
        ('mid', 'Orta Sezon'),
        ('high', 'Yüksek Sezon'),
        ('peak', 'Pik Sezon')
    ], string='Sezon Tipi')
    
    # Tarih bazlı en iyi teklifler
    best_offer_amount = fields.Monetary(
        compute='_compute_best_offer',
        store=True,
        string='En İyi Teklif',
        currency_field='currency_id'
    )
    
    best_offer_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_best_offer',
        store=True,
        string='En İyi Teklif Veren'
    )
    
    offer_count = fields.Integer(
        compute='_compute_offer_count',
        string='Teklif Sayısı'
    )
    
    @api.depends('date_start', 'date_end')
    def _compute_name(self):
        for record in self:
            if record.date_start and record.date_end:
                # Odoo'nun babel formatını kullan
                start_str = record.date_start.strftime('%d %b')
                end_str = record.date_end.strftime('%d %b %Y')
                record.name = f"{start_str} - {end_str}"
            else:
                record.name = _("Tarih Belirtilmedi")
    
    @api.depends('date_start', 'date_end')
    def _compute_days(self):
        for record in self:
            if record.date_start and record.date_end:
                delta = record.date_end - record.date_start
                record.days = delta.days + 1  # +1 çünkü başlangıç günü dahil
            else:
                record.days = 0
    
    def _compute_best_offer(self):
        """Bu tarih için en iyi teklifi hesapla"""
        for date_option in self:
            po_lines = self.env['purchase.order.line'].search([
                ('scenario_date_id', '=', date_option.id),
                ('order_id.state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
            ])
            
            if po_lines:
                # Tedarikçi bazında topla
                partner_totals = {}
                for line in po_lines:
                    partner_id = line.order_id.partner_id.id
                    if partner_id not in partner_totals:
                        partner_totals[partner_id] = {
                            'total': 0.0,
                            'partner': line.order_id.partner_id
                        }
                    partner_totals[partner_id]['total'] += line.price_subtotal
                
                if partner_totals:
                    best = min(partner_totals.values(), key=lambda x: x['total'])
                    date_option.best_offer_amount = best['total']
                    date_option.best_offer_partner_id = best['partner']
                else:
                    date_option.best_offer_amount = 0.0
                    date_option.best_offer_partner_id = False
            else:
                date_option.best_offer_amount = 0.0
                date_option.best_offer_partner_id = False
    
    def _compute_offer_count(self):
        """Bu tarih için kaç teklif alındığını say"""
        for date_option in self:
            # Benzersiz tedarikçi sayısı
            po_lines = self.env['purchase.order.line'].search([
                ('scenario_date_id', '=', date_option.id),
                ('order_id.state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
            ])
            unique_partners = po_lines.mapped('order_id.partner_id')
            date_option.offer_count = len(unique_partners)
    
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_start > record.date_end:
                raise ValidationError(_('Başlangıç tarihi bitiş tarihinden sonra olamaz!'))
    
    def action_view_offers(self):
        """Bu tarih için verilen teklifleri görüntüle"""
        self.ensure_one()
        return {
            'name': f'{self.name} - Teklifler',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'tree',
            'domain': [('scenario_date_id', '=', self.id)],
            'context': {'group_by': 'order_id'}
        }
