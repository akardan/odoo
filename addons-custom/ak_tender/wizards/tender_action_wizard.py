# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TenderActionWizard(models.TransientModel):
    _name = 'ak.tender.action.wizard'
    _description = 'İhale İşlem Sihirbazı'

    tender_id = fields.Many2one('ak.tender', string='İhale', required=True)
    action_type = fields.Selection([
        ('start_first_round', '1. Teklif Toplamayı Başlat'),
        ('set_target_price', 'Hedef Fiyatı Belirle'),
        ('start_second_round', '2. Teklif Toplamayı Başlat'),
        ('to_evaluation', 'Değerlendirmeye Geç'),
        ('request_approval', 'Onay Talep Et'),
        ('approve_tender', 'İhaleyi Onayla'),
        ('complete_tender', 'İhaleyi Tamamla'),
        ('cancel_tender', 'İptal Et'),
        ('set_draft', 'Taslağa Çevir'),
    ], string='Yapılacak İşlem', required=True)
    
    notes = fields.Text(string='Notlar')
    
    def confirm_action(self):
        self.ensure_one()
        tender = self.tender_id
        
        if self.action_type == 'start_first_round':
            tender.action_start_first_round()
        elif self.action_type == 'set_target_price':
            tender.action_set_target_price()
        elif self.action_type == 'start_second_round':
            tender.action_start_second_round()
        elif self.action_type == 'to_evaluation':
            tender.action_to_evaluation()
        elif self.action_type == 'request_approval':
            tender.action_request_approval()
        elif self.action_type == 'approve_tender':
            tender.action_approve_tender()
        elif self.action_type == 'complete_tender':
            tender.action_complete_tender()
        elif self.action_type == 'cancel_tender':
            tender.action_cancel_tender()
        elif self.action_type == 'set_draft':
            tender.action_set_draft()
        else:
            raise UserError(_("Geçersiz işlem tipi."))
            
        return {'type': 'ir.actions.act_window_close'}

