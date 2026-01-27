# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AkTenderScenario(models.Model):
    _name = 'ak.tender.scenario'
    _description = 'İhale Alternatif Senaryosu'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    
    # ===== TEMEL BİLGİLER =====
    tender_id = fields.Many2one('ak.tender', required=True, ondelete='cascade', string='İhale')
    name = fields.Char(string='Senaryo Adı', required=True)
    # Örn: "Chamada Prestige 5⭐ (Antalya) - Yarım Pansiyon"
    
    sequence = fields.Integer(default=10, string='Sıra')
    active = fields.Boolean(default=True, string='Aktif')
    
    scenario_type = fields.Selection([
        ('location_hotel', 'Lokasyon-Otel Paketi'),
        ('transfer', 'Transfer Paketi'),
        ('meal', 'Yemek Paketi'),
        ('technical', 'Teknik Paket'),
        ('flight', 'Uçuş Paketi'),
        ('custom', 'Özel Paket')
    ], string='Senaryo Tipi', default='location_hotel')
    
    # ===== LOKASYON VE OTEL =====
    location_id = fields.Many2one('res.country.state', string='Lokasyon')
    hotel_partner_id = fields.Many2one('res.partner', string='Otel',
                                       domain=[('is_company', '=', True)])
    
    # ===== MICE ÖZEL ALANLAR =====
    meal_plan = fields.Selection([
        ('ro', 'Room Only'),
        ('bb', 'Bed & Breakfast'),
        ('hb', 'Half Board'),
        ('fb', 'Full Board'),
        ('ai', 'All Inclusive'),
        ('uai', 'Ultra All Inclusive')
    ], string='Pansiyon Tipi')
    
    person_count = fields.Integer(string='Kişi Sayısı')
    vip_count = fields.Integer(string='VIP Sayısı')
    
    # ===== TARİH SEÇENEKLERİ =====
    date_option_ids = fields.One2many(
        'ak.tender.scenario.date',
        'scenario_id',
        string='Alternatif Tarihler'
    )
    
    # ===== KALEMLER =====
    line_ids = fields.One2many('ak.tender.line', 'scenario_id', string='Kalemler')
    line_count = fields.Integer(compute='_compute_line_count', string='Kalem Sayısı')
    
    # ===== FİYATLANDIRMA =====
    currency_id = fields.Many2one(related='tender_id.currency_id', string='Para Birimi')
    total_target_price = fields.Monetary(
        compute='_compute_total_target',
        store=True,
        string='Toplam Hedef Fiyat',
        currency_field='currency_id'
    )
    
    # ===== SENARYO KAYNAĞI =====
    scenario_source = fields.Selection([
        ('buyer', 'Alıcı Talebi'),
        ('supplier_counter', 'Tedarikçi Karşı Teklifi')
    ], default='buyer', string='Kaynak')
    
    supplier_id = fields.Many2one('res.partner', string='Öneren Tedarikçi',
                                  help='Karşı teklif ise hangi tedarikçi önerdi?')
    
    # ===== ZORUNLULUK =====
    is_mandatory = fields.Boolean(
        string='Zorunlu Senaryo',
        default=False,
        help='Tedarikçiler bu senaryoya mutlaka teklif vermeli mi?'
    )
    
    # ===== KISA LİSTE MEKANİZMASI =====
    is_shortlisted = fields.Boolean(string='Kısa Listede', default=False)
    shortlist_round = fields.Integer(string='Kısa Listeye Alınma Turu')
    shortlist_date = fields.Datetime(string='Kısa Liste Tarihi', readonly=True)
    shortlist_by = fields.Many2one('res.users', string='Kısa Listeye Ekleyen', readonly=True)
    shortlist_notes = fields.Text(string='Kısa Liste Notları')
    
    scenario_status = fields.Selection([
        ('active', 'Aktif - Teklif Alınıyor'),
        ('shortlisted', 'Kısa Listede'),
        ('eliminated', 'Elendi'),
        ('awarded', 'Kazanan')
    ], default='active', string='Durum', required=True)
    
    elimination_reason = fields.Text(string='Eleme Gerekçesi')
    
    # ===== TUR BAZLI EN İYİ TEKLİFLER =====
    best_offer_round_1 = fields.Monetary(
        compute='_compute_best_offers',
        store=True,
        string='Tur 1 En İyi Teklif',
        currency_field='currency_id'
    )
    
    best_offer_round_2 = fields.Monetary(
        compute='_compute_best_offers',
        store=True,
        string='Tur 2 En İyi Teklif',
        currency_field='currency_id'
    )
    
    improvement_percentage = fields.Float(
        compute='_compute_improvement',
        store=True,
        string='İyileştirme %',
        help='Tur 2 vs Tur 1 fiyat iyileştirmesi'
    )
    
    # ===== NPV BAZLI EN İYİ TEKLİFLER =====
    best_npv_offer = fields.Monetary(
        'En İyi NPV Teklif',
        compute='_compute_best_npv_offer',
        store=True,
        currency_field='currency_id',
        help='NPV bazında en düşük teklif'
    )
    
    best_npv_partner_id = fields.Many2one(
        'res.partner',
        'En İyi NPV Tedarikçi',
        compute='_compute_best_npv_offer',
        store=True
    )
    
    # ===== COMPUTED FIELDS =====
    @api.depends('line_ids')
    def _compute_line_count(self):
        for scenario in self:
            scenario.line_count = len(scenario.line_ids)
    
    @api.depends('line_ids.computed_target_total')
    def _compute_total_target(self):
        for scenario in self:
            scenario.total_target_price = sum(scenario.line_ids.mapped('computed_target_total'))
    
    @api.depends('line_ids')
    def _compute_best_offers(self):
        """Her tur için en düşük teklifi hesapla"""
        for scenario in self:
            po_lines = self.env['purchase.order.line'].search([
                ('tender_line_id.scenario_id', '=', scenario.id),
                ('order_id.state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
            ])
            
            round_1_lines = po_lines.filtered(lambda l: l.order_id.tender_round == 1)
            round_2_lines = po_lines.filtered(lambda l: l.order_id.tender_round == 2)
            
            if round_1_lines:
                # Tedarikçi bazında topla
                partner_totals_r1 = {}
                for line in round_1_lines:
                    partner_id = line.order_id.partner_id.id
                    if partner_id not in partner_totals_r1:
                        partner_totals_r1[partner_id] = 0.0
                    partner_totals_r1[partner_id] += line.price_subtotal
                scenario.best_offer_round_1 = min(partner_totals_r1.values()) if partner_totals_r1 else 0.0
            else:
                scenario.best_offer_round_1 = 0.0
            
            if round_2_lines:
                partner_totals_r2 = {}
                for line in round_2_lines:
                    partner_id = line.order_id.partner_id.id
                    if partner_id not in partner_totals_r2:
                        partner_totals_r2[partner_id] = 0.0
                    partner_totals_r2[partner_id] += line.price_subtotal
                scenario.best_offer_round_2 = min(partner_totals_r2.values()) if partner_totals_r2 else 0.0
            else:
                scenario.best_offer_round_2 = 0.0
    
    @api.depends('best_offer_round_1', 'best_offer_round_2')
    def _compute_improvement(self):
        for scenario in self:
            if scenario.best_offer_round_1 and scenario.best_offer_round_2:
                improvement = scenario.best_offer_round_1 - scenario.best_offer_round_2
                scenario.improvement_percentage = (improvement / scenario.best_offer_round_1) * 100
            else:
                scenario.improvement_percentage = 0.0
    
    @api.depends('line_ids')
    def _compute_best_npv_offer(self):
        """Bu senaryo için NPV bazında en iyi teklifi bul"""
        for scenario in self:
            # Bu senaryoya ait tüm PO line'ları bul
            po_lines = self.env['purchase.order.line'].search([
                ('tender_line_id.scenario_id', '=', scenario.id),
                ('order_id.state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
            ])
            
            if po_lines:
                # Tedarikçi bazında NPV toplamlarını hesapla
                partner_npv = {}
                for line in po_lines:
                    partner_id = line.order_id.partner_id.id
                    if partner_id not in partner_npv:
                        partner_npv[partner_id] = {
                            'total_npv': 0.0,
                            'partner': line.order_id.partner_id
                        }
                    partner_npv[partner_id]['total_npv'] += line.price_npv
                
                # En düşük NPV'yi bul
                if partner_npv:
                    best = min(partner_npv.values(), key=lambda x: x['total_npv'])
                    scenario.best_npv_offer = best['total_npv']
                    scenario.best_npv_partner_id = best['partner']
                else:
                    scenario.best_npv_offer = 0.0
                    scenario.best_npv_partner_id = False
            else:
                scenario.best_npv_offer = 0.0
                scenario.best_npv_partner_id = False
    
    # ===== ACTIONS =====
    def action_add_to_shortlist(self):
        """Senaryoyu kısa listeye ekle"""
        self.ensure_one()
        self.write({
            'is_shortlisted': True,
            'scenario_status': 'shortlisted',
            'shortlist_round': self.tender_id.tender_round,
            'shortlist_date': fields.Datetime.now(),
            'shortlist_by': self.env.user.id
        })
        return True
    
    def action_eliminate_scenario(self):
        """Senaryoyu elenle"""
        self.ensure_one()
        return {
            'name': 'Senaryo Eleme',
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.eliminate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scenario_id': self.id}
        }
    
    def action_view_comparison(self):
        """Senaryo detaylı karşılaştırma"""
        self.ensure_one()
        return {
            'name': f'Karşılaştırma: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'list',
            'domain': [('tender_line_id.scenario_id', '=', self.id)],
            'context': {'group_by': 'order_id'}
        }
    
    def action_view_lines(self):
        """Senaryo kalemlerini görüntüle"""
        self.ensure_one()
        return {
            'name': f'{self.name} - Kalemler',
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.line',
            'view_mode': 'list,form',
            'domain': [('scenario_id', '=', self.id)],
            'context': {
                'default_scenario_id': self.id,
                'default_tender_id': self.tender_id.id
            }
        }
