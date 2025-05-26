# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SetTargetPriceWizard(models.TransientModel):
    _name = 'ak.tender.set.target.price.wizard'
    _description = 'Hedef Fiyat Belirleme Sihirbazı'

    tender_id = fields.Many2one('ak.tender', string='İhale', required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='tender_id.currency_id', readonly=True)
    target_price = fields.Monetary(string='Hedef Fiyat', currency_field='currency_id', required=True,
                                  help="Satın Alma Direktörü tarafından belirlenen hedef fiyat.")
    
    @api.model
    def default_get(self, fields_list):
        res = super(SetTargetPriceWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            tender = self.env['ak.tender'].browse(active_id)
            res['tender_id'] = tender.id
            if tender.target_price > 0:
                res['target_price'] = tender.target_price
        return res
    
    def action_confirm(self):
        self.ensure_one()
        tender = self.tender_id
        
        if tender.state != 'first_tender_round':
            raise UserError(_("Hedef fiyat sadece '1. Teklif Toplama' aşamasında belirlenebilir."))
        if not tender.tender_results:
            raise UserError(_("Hedef fiyat belirlemek için en az bir teklif sonucu girilmelidir."))
        if not self.target_price or self.target_price <= 0:
            raise UserError(_("Lütfen geçerli bir hedef fiyat girin."))
        
        # Hedef fiyatı güncelle ve durumu değiştir
        tender.write({
            'target_price': self.target_price,
            'state': 'target_price_set'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hedef Fiyat Belirlendi'),
                'message': _('İhale için hedef fiyat belirlendi. İkinci teklif toplama turu için hazır.'),
                'sticky': False,
            }
        }