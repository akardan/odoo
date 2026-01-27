# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SetTargetPriceWizard(models.TransientModel):
    _name = 'ak.tender.set.target.price.wizard'
    _description = _('Hedef Fiyat Belirleme Sihirbazı')

    tender_id = fields.Many2one('ak.tender', string=_('İhale'), required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='tender_id.currency_id', readonly=True)
    target_price = fields.Monetary(string=_('Hedef Fiyat'), currency_field='currency_id', required=True,
                                  help=_("Satın Alma Direktörü tarafından belirlenen hedef fiyat."))
    
    @api.model
    def default_get(self, fields_list):
        res = super(SetTargetPriceWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        tender_id = self.env.context.get('default_tender_id')
        if tender_id:
            tender = self.env['ak.tender'].browse(tender_id)
            res['tender_id'] = tender.id
            if tender.target_price > 0:
                res['target_price'] = tender.target_price
        elif active_id:
            tender = self.env['ak.tender'].browse(active_id)
            res['tender_id'] = tender.id
            if tender.target_price > 0:
                res['target_price'] = tender.target_price
        return res
    
    def action_confirm(self):
        self.ensure_one()
        tender = self.tender_id
        
        if not tender.workflow_current_state_id or tender.workflow_current_state_id.code != 'target_price_set':
            raise UserError(_("Hedef fiyat sadece 'Hedef Fiyat Belirleme' aşamasında belirlenebilir."))
        if not tender.purchase_order_ids:
            raise UserError(_("Hedef fiyat belirlemek için en az bir teklif girilmelidir."))
        if not self.target_price or self.target_price <= 0:
            raise UserError(_("Lütfen geçerli bir hedef fiyat girin."))
        
        # Hedef fiyatı güncelle
        tender.write({
            'target_price': self.target_price,
        })
        
        # Hedef fiyat belirleme durumundayız, sadece fiyatı güncelle
        if tender.workflow_current_state_id.code == 'target_price_set':
            # Sadece mesaj gönder
            tender.message_post(
                body=_("Hedef fiyat güncellendi: %s") % self.target_price,
                subtype_xmlid='mail.mt_note'
            )
        else:
            # Workflow geçişini bul ve uygula
            target_price_transition = self.env['ak.workflow.transition'].search([
                ('from_state_id', '=', tender.workflow_current_state_id.id),
                ('to_state_id.code', '=', 'target_price_set')
            ], limit=1)
            
            if target_price_transition:
                tender.execute_transition(target_price_transition.id, _("Hedef fiyat belirlendi: %s") % self.target_price)
            else:
                raise UserError(_("Hedef fiyat belirleme geçişi bulunamadı. Lütfen iş akışı tanımını kontrol edin."))
        
        # Başarı mesajını duruma göre ayarla
        if tender.workflow_current_state_id.code == 'target_price_set':
            title = _('Hedef Fiyat Güncellendi')
            message = _('İhale için hedef fiyat güncellendi.')
        else:
            title = _('Hedef Fiyat Belirlendi')
            message = _('İhale için hedef fiyat belirlendi. Yeni bir teklif toplama turu için hazır.')
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
            }
        }