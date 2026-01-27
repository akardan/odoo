# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AkTender(models.Model):
    _inherit = 'ak.tender'
    
    # ===== SENARYO İLİŞKİSİ =====
    scenario_ids = fields.One2many('ak.tender.scenario', 'tender_id', string='Senaryolar')
    scenario_count = fields.Integer(compute='_compute_scenario_count', string='Senaryo Sayısı')
    
    # ===== SENARYO İSTATİSTİKLERİ =====
    total_scenarios = fields.Integer(compute='_compute_scenario_stats', string='Toplam Senaryo')
    shortlisted_scenarios = fields.Integer(compute='_compute_scenario_stats', string='Kısa Liste')
    eliminated_scenarios = fields.Integer(compute='_compute_scenario_stats', string='Elenen')
    awarded_scenarios = fields.Integer(compute='_compute_scenario_stats', string='Kazanan')
    
    # ===== MICE ÖZEL ALANLAR =====
    total_person_count = fields.Integer(string='Toplam Kişi Sayısı')
    vip_person_count = fields.Integer(string='VIP Kişi Sayısı')
    
    @api.depends('scenario_ids')
    def _compute_scenario_count(self):
        for tender in self:
            tender.scenario_count = len(tender.scenario_ids)
    
    @api.depends('scenario_ids.scenario_status')
    def _compute_scenario_stats(self):
        for tender in self:
            tender.total_scenarios = len(tender.scenario_ids)
            tender.shortlisted_scenarios = len(
                tender.scenario_ids.filtered(lambda s: s.is_shortlisted)
            )
            tender.eliminated_scenarios = len(
                tender.scenario_ids.filtered(lambda s: s.scenario_status == 'eliminated')
            )
            tender.awarded_scenarios = len(
                tender.scenario_ids.filtered(lambda s: s.scenario_status == 'awarded')
            )
    
    def action_start_next_round(self):
        """Sonraki turu başlat (sadece kısa listedeki senaryolar için)"""
        self.ensure_one()
        
        shortlisted = self.scenario_ids.filtered(lambda s: s.is_shortlisted)
        
        if not shortlisted:
            raise UserError(_("Kısa listeye alınmış senaryo yok!"))
        
        return {
            'name': _('Yeni Tur Başlat'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.next.round.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
                'default_next_round': self.tender_round + 1,
                'default_shortlisted_scenario_ids': shortlisted.ids
            }
        }
    
    # DISABLED FOR PRODUCTION - MICE Feature
    # def action_view_scenarios(self):
    #     """Senaryoları görüntüle"""
    #     self.ensure_one()
    #
    #     tree_view_id = self.env.ref('ak_tender.view_tender_scenario_tree').id
    #     form_view_id = self.env.ref('ak_tender.view_tender_scenario_form').id
    #     kanban_view_id = self.env.ref('ak_tender.view_tender_scenario_kanban').id
    #
    #     return {
    #         'name': f'{self.name} - ' + _('Senaryolar'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'ak.tender.scenario',
    #         'view_mode': 'list,form,kanban',
    #         'views': [
    #             (tree_view_id, 'list'),
    #             (form_view_id, 'form'),
    #             (kanban_view_id, 'kanban')
    #         ],
    #         'domain': [('tender_id', '=', self.id)],
    #         'context': {'default_tender_id': self.id}
    #     }
    
    def action_create_scenario(self):
        """Yeni senaryo oluştur"""
        self.ensure_one()
        return {
            'name': _('Yeni Senaryo Oluştur'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tender_id': self.id}
        }


class AkTenderLine(models.Model):
    _inherit = 'ak.tender.line'
    
    # ===== SENARYO İLİŞKİSİ =====
    scenario_id = fields.Many2one('ak.tender.scenario', string='Senaryo', ondelete='cascade')
    
    # Geriye dönük uyumluluk için
    alternative_group_id = fields.Integer(
        related='scenario_id.id',
        store=True,
        string='Alternatif Grup ID'
    )
    
    # ===== SATIR TİPİ =====
    line_type = fields.Selection([
        ('accommodation', 'Konaklama'),
        ('meal', 'Yemek'),
        ('transfer', 'Transfer'),
        ('technical', 'Teknik Hizmet'),
        ('flight', 'Uçuş'),
        ('service', 'Diğer Hizmet'),
        ('package', 'Paket')
    ], string='Satır Tipi')
    
    # ===== MICE ÖZEL ALANLAR (JSON'a taşınabilir) =====
    mice_room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('suite', 'Suite'),
        ('presidential', 'Presidential Suite')
    ], string='Oda Tipi')
    
    mice_view_type = fields.Selection([
        ('city', 'Şehir Manzarası'),
        ('sea', 'Deniz Manzarası'),
        ('mountain', 'Dağ Manzarası'),
        ('garden', 'Bahçe Manzarası'),
        ('pool', 'Havuz Manzarası')
    ], string='Manzara')
    
    mice_meal_plan = fields.Selection([
        ('ro', 'Room Only'),
        ('bb', 'Bed & Breakfast'),
        ('hb', 'Half Board'),
        ('fb', 'Full Board'),
        ('ai', 'All Inclusive'),
        ('uai', 'Ultra All Inclusive')
    ], string='Pansiyon Tipi')
    
    mice_amenities = fields.Char(
        'Özel Hizmetler',
        help='Virgülle ayrılmış: WiFi, Havuz, Spa, Butler, Minibar'
    )
    
    mice_special_requests = fields.Text(
        'Özel İstekler',
        help='Özel talepler ve notlar'
    )
    
    # ===== HESAPLANAN TOPLAM =====
    computed_target_total = fields.Monetary(
        compute='_compute_target_total',
        store=True,
        string='Toplam Hedef',
        help='Miktar × Gün × Birim Fiyat',
        currency_field='currency_id'
    )
    
    # ===== ÖZET BİLGİ =====
    line_summary = fields.Text(
        'Özet Bilgi',
        compute='_compute_line_summary',
        store=True,
        help='Otomatik oluşturulan kullanıcı dostu özet'
    )
    
    @api.depends('quantity', 'days', 'target_price')
    def _compute_target_total(self):
        for line in self:
            line.computed_target_total = line.quantity * line.days * line.target_price
    
    @api.depends('mice_room_type', 'mice_view_type', 'mice_amenities',
                 'scenario_id.meal_plan', 'scenario_id.hotel_partner_id', 'name')
    def _compute_line_summary(self):
        """Otomatik özet oluştur"""
        for line in self:
            if line.scenario_id and line.scenario_id.tender_id.tender_type == 'mice':
                summary_parts = []
                
                # Otel bilgisi
                if line.scenario_id.hotel_partner_id:
                    summary_parts.append(line.scenario_id.hotel_partner_id.name)
                
                # Oda tipi
                if line.mice_room_type:
                    room_dict = dict(line._fields['mice_room_type'].selection)
                    summary_parts.append(room_dict.get(line.mice_room_type, ''))
                
                # Pansiyon (senaryodan)
                if line.scenario_id.meal_plan:
                    meal_dict = dict(line.scenario_id._fields['meal_plan'].selection)
                    summary_parts.append(meal_dict.get(line.scenario_id.meal_plan, ''))
                
                # Manzara
                if line.mice_view_type:
                    view_dict = dict(line._fields['mice_view_type'].selection)
                    summary_parts.append(view_dict.get(line.mice_view_type, ''))
                
                # Özellikler (ilk 3 tanesini göster)
                if line.mice_amenities:
                    amenities = line.mice_amenities.split(',')[:3]
                    summary_parts.append(f"({', '.join([a.strip() for a in amenities])})")
                
                line.line_summary = ' | '.join(summary_parts)
            else:
                line.line_summary = line.name or ''
    
    @api.onchange('mice_room_type', 'mice_view_type', 'mice_amenities')
    def _onchange_mice_fields(self):
        """MICE alanları değiştiğinde özet güncelle"""
        # Compute method otomatik çalışacak
        pass
