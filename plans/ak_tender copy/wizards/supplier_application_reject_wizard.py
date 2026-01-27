# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SupplierApplicationRejectWizard(models.TransientModel):
    _name = 'supplier.application.reject.wizard'
    _description = 'Reject Supplier Application'
    
    application_id = fields.Many2one('supplier.application', string='Application', required=True)
    rejection_reason = fields.Text('Rejection Reason', required=True,
                                    help='Please provide a clear reason for rejection')
    send_email = fields.Boolean('Send Email to Applicant', default=True,
                                 help='Notify the applicant about the rejection')
    
    def action_confirm_reject(self):
        """Confirm rejection and update application"""
        self.ensure_one()
        
        if not self.rejection_reason:
            raise ValidationError(_('Please provide a rejection reason.'))
        
        # Update application
        self.application_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        
        # Send rejection email if requested
        if self.send_email:
            self._send_rejection_email()
        
        # Log message
        self.application_id.message_post(
            body=_('Application rejected. Reason: %s') % self.rejection_reason,
            subject=_('Application Rejected'),
        )
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _send_rejection_email(self):
        """Send rejection notification email"""
        template = self.env.ref('ak_tender.email_template_supplier_application_rejected',
                                raise_if_not_found=False)
        if template:
            template.send_mail(self.application_id.id, 
                             email_values={'email_to': self.application_id.contact_email})