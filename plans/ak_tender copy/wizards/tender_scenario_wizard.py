# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TenderScenarioWizard(models.TransientModel):
    _name = 'ak.tender.scenario.wizard'
    _description = 'Senaryo Oluşturma Sihirbazı'
    
    tender_id = fields.Many2one('ak.tender', string='İhale', required=True)
    name = fields.Char(string='Senaryo Adı', required=True)
    scenario_type = fields.Selection([
        ('location_hotel', 'Lokasyon-Otel Paketi'),
        ('transfer', 'Transfer Paketi'),
        ('meal', 'Yemek Paketi'),
        ('technical', 'Teknik Paket'),
        ('flight', 'Uçuş Paketi'),
        ('custom', 'Özel Paket')
    ], string='Senaryo Tipi', default='location_hotel', required=True)
    
    location_id = fields.Many2one('res.country.state', string='Lokasyon')
    hotel_partner_id = fields.Many2one('res.partner', string='Otel',
                                       domain=[('is_company', '=', True)])
    
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
    is_mandatory = fields.Boolean(string='Zorunlu Senaryo', default=False)
    
    # Tarih seçenekleri
    add_dates = fields.Boolean(string='Tarih Seçenekleri Ekle', default=True)
    date_option_ids = fields.One2many(
        'ak.tender.scenario.wizard.date',
        'wizard_id',
        string='Tarih Seçenekleri'
    )
    
    def action_create_scenario(self):
        """Senaryoyu oluştur"""
        self.ensure_one()
        
        # Senaryo oluştur
        scenario_vals = {
            'tender_id': self.tender_id.id,
            'name': self.name,
            'scenario_type': self.scenario_type,
            'location_id': self.location_id.id if self.location_id else False,
            'hotel_partner_id': self.hotel_partner_id.id if self.hotel_partner_id else False,
            'meal_plan': self.meal_plan,
            'person_count': self.person_count,
            'vip_count': self.vip_count,
            'is_mandatory': self.is_mandatory,
            'scenario_source': 'buyer',
        }
        
        scenario = self.env['ak.tender.scenario'].create(scenario_vals)
        
        # Tarih seçeneklerini ekle
        if self.add_dates and self.date_option_ids:
            for date_line in self.date_option_ids:
                self.env['ak.tender.scenario.date'].create({
                    'scenario_id': scenario.id,
                    'date_start': date_line.date_start,
                    'date_end': date_line.date_end,
                    'season_type': date_line.season_type,
                    'cost_multiplier': date_line.cost_multiplier,
                    'estimated_total_cost': date_line.estimated_total_cost,
                    'is_preferred': date_line.is_preferred,
                    'notes': date_line.notes,
                })
        
        # Senaryoyu aç
        return {
            'name': _('Senaryo: %s') % scenario.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario',
            'res_id': scenario.id,
            'view_mode': 'form',
            'target': 'current',
        }


class TenderScenarioWizardDate(models.TransientModel):
    _name = 'ak.tender.scenario.wizard.date'
    _description = 'Senaryo Wizard Tarih Seçeneği'
    
    wizard_id = fields.Many2one('ak.tender.scenario.wizard', required=True, ondelete='cascade')
    date_start = fields.Date(string='Başlangıç', required=True)
    date_end = fields.Date(string='Bitiş', required=True)
    season_type = fields.Selection([
        ('low', 'Düşük Sezon'),
        ('mid', 'Orta Sezon'),
        ('high', 'Yüksek Sezon'),
        ('peak', 'Pik Sezon')
    ], string='Sezon Tipi')
    cost_multiplier = fields.Float(string='Maliyet Çarpanı', default=1.0)
    estimated_total_cost = fields.Monetary(string='Tahmini Maliyet', currency_field='currency_id')
    currency_id = fields.Many2one(related='wizard_id.tender_id.currency_id')
    is_preferred = fields.Boolean(string='Tercih Edilen')
    notes = fields.Text(string='Notlar')


class TenderScenarioEliminateWizard(models.TransientModel):
    _name = 'ak.tender.scenario.eliminate.wizard'
    _description = 'Senaryo Eleme Sihirbazı'
    
    scenario_id = fields.Many2one('ak.tender.scenario', string='Senaryo', required=True)
    elimination_reason = fields.Text(string='Eleme Gerekçesi', required=True)
    
    def action_eliminate(self):
        """Senaryoyu elenle"""
        self.ensure_one()
        self.scenario_id.write({
            'scenario_status': 'eliminated',
            'is_shortlisted': False,
            'elimination_reason': self.elimination_reason,
        })
        return {'type': 'ir.actions.act_window_close'}


class TenderNextRoundWizard(models.TransientModel):
    _name = 'ak.tender.next.round.wizard'
    _description = 'Sonraki Tur Sihirbazı'
    
    tender_id = fields.Many2one('ak.tender', string='İhale', required=True)
    next_round = fields.Integer(string='Yeni Tur', required=True)
    shortlisted_scenario_ids = fields.Many2many(
        'ak.tender.scenario',
        string='Kısa Listedeki Senaryolar',
        domain="[('tender_id', '=', tender_id), ('is_shortlisted', '=', True)]"
    )
    
    invite_all_suppliers = fields.Boolean(
        string='Tüm Tedarikçileri Davet Et',
        default=False,
        help='Tüm tedarikçileri davet et, yoksa sadece teklif verenleri davet et'
    )
    
    deadline_days = fields.Integer(string='Süre (Gün)', default=5)
    notes = fields.Text(string='Notlar')
    
    def action_start_round(self):
        """Yeni turu başlat"""
        self.ensure_one()
        
        if not self.shortlisted_scenario_ids:
            raise UserError(_('Kısa listeye alınmış senaryo seçmelisiniz!'))
        
        # İhale turunu güncelle
        self.tender_id.write({
            'tender_round': self.next_round,
        })
        
        # Tedarikçilere bildirim gönder (mail template ile)
        # TODO: Mail template oluşturulacak
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Başarılı'),
                'message': _('Tur %s başlatıldı. %s senaryo için teklifler bekleniyor.') % (
                    self.next_round,
                    len(self.shortlisted_scenario_ids)
                ),
                'type': 'success',
                'sticky': False,
            }
        }
