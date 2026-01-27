# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AddSupplierWizard(models.TransientModel):
    _name = 'ak.tender.add.supplier.wizard'
    _description = _('Tedarikçi Ekleme Sihirbazı')

    tender_id = fields.Many2one('ak.tender', string=_('İhale'), required=True,
                               readonly=True)
    partner_ids = fields.Many2many('res.partner', string=_('Tedarikçiler'),
                                  domain=[('supplier_rank', '>=', 0)],
                                  required=True,
                                  help=_("İhaleye eklenecek tedarikçiler."))
    send_invitation = fields.Boolean(string=_('Davet Gönder'), default=True,
                                    help=_("Tedarikçilere otomatik davet e-postası gönder."))
    invitation_message = fields.Html(string=_('Davet Mesajı'),
                                    help=_("Tedarikçilere gönderilecek davet mesajı."))
    
    @api.model
    def default_get(self, fields_list):
        """
        Set default values for the wizard.
        """
        res = super(AddSupplierWizard, self).default_get(fields_list)
        
        # Get the active tender
        active_id = self.env.context.get('active_id')
        if active_id:
            tender = self.env['ak.tender'].browse(active_id)
            res['tender_id'] = tender.id
            
            # Set default invitation message
            res['invitation_message'] = f"""
                <p>Sayın Tedarikçimiz,</p>
                <p>İLKOis tarafından düzenlenen <strong>{tender.name}</strong> ihalesine davet edildiniz.</p>
                <p>İhale detayları için lütfen portal hesabınızı kontrol ediniz.</p>
                <p>Saygılarımızla,<br/>İLKOis Satın Alma Ekibi</p>
            """
        
        return res
    
    def action_add_suppliers(self):
        """
        Add the selected suppliers to the tender.
        """
        self.ensure_one()
        
        if not self.partner_ids:
            raise ValidationError(_("En az bir tedarikçi seçmelisiniz."))
            
        # Add suppliers to the tender
        current_partners = self.tender_id.invited_partners
        new_partners = self.partner_ids - current_partners
        
        if not new_partners:
            raise ValidationError(_("Seçilen tedarikçiler zaten ihaleye davet edilmiş."))
            
        self.tender_id.write({
            'invited_partners': [(4, partner.id) for partner in new_partners]
        })
        
        # Send invitation emails if requested
        if self.send_invitation:
            self._send_invitation_emails(new_partners)
            
        # Log the addition
        partner_names = ", ".join(new_partners.mapped('name'))
        self.tender_id.message_post(
            body=_("Yeni tedarikçiler ihaleye eklendi: %s") % partner_names,
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tedarikçiler Eklendi'),
                'message': _('%s tedarikçi ihaleye başarıyla eklendi.') % len(new_partners),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def _send_invitation_emails(self, partners):
        """
        Send invitation emails to the added suppliers.
        This is a simulated method for the prototype.
        In a real implementation, this would send actual emails.
        """
        # Log the email sending
        self.tender_id.message_post(
            body=_("Davet e-postaları gönderildi: %s") % ", ".join(partners.mapped('name')),
            subtype_xmlid='mail.mt_note'
        )
        
        return True