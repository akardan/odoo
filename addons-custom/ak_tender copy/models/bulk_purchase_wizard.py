# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BulkPurchaseWizard(models.TransientModel):
    _name = 'ak.tender.bulk.purchase.wizard'
    _description = _('Toplu Satın Alma Sihirbazı')

    name = fields.Char(string=_('İhale Adı'), required=True,
                      help=_("Oluşturulacak ihalenin adı."))
    tender_type = fields.Selection([
        ('indirect', _('Endirekt Satın Alma')),
        ('promotion', _('Promosyon ve Kırtasiye'))
    ], string=_('İhale Tipi'), default='indirect', required=True,
        help=_("Oluşturulacak ihalenin tipi."))
    pr_ids = fields.Char(string=_('SAT Numaraları'), required=True,
                        help=_("Birleştirilecek SAT numaraları (virgülle ayrılmış)."))
    
    @api.onchange('pr_ids')
    def _onchange_pr_ids(self):
        """Update the name based on the PR IDs."""
        if self.pr_ids:
            pr_list = [pr.strip() for pr in self.pr_ids.split(',') if pr.strip()]
            if pr_list:
                if len(pr_list) <= 3:
                    self.name = _("Toplu Satın Alma: %s") % ', '.join(pr_list)
                else:
                    self.name = _("Toplu Satın Alma: %s ve %s diğer") % (
                        ', '.join(pr_list[:3]), len(pr_list) - 3)
    
    def action_create_bulk_tender(self):
        """Create a bulk purchase tender."""
        self.ensure_one()
        
        if not self.pr_ids:
            raise ValidationError(_("En az bir SAT numarası belirtilmelidir."))
        
        pr_list = [pr.strip() for pr in self.pr_ids.split(',') if pr.strip()]
        if not pr_list:
            raise ValidationError(_("Geçerli SAT numaraları belirtilmelidir."))
        
        # Check minimum requirements
        min_items = int(self.env['ir.config_parameter'].sudo().get_param(
            'ak_tender_bulk_purchase_min_items', default=3))
        
        if len(pr_list) < min_items:
            raise ValidationError(_(
                "Toplu satın alma için en az %s SAT numarası belirtilmelidir.") % min_items)
        
        # Create the tender
        tender = self.env['ak.tender'].create_bulk_purchase_tender(
            pr_list, name=self.name, tender_type=self.tender_type)
        
        # Show the created tender
        return {
            'name': _('Toplu Satın Alma İhalesi'),
            'view_mode': 'form',
            'res_model': 'ak.tender',
            'res_id': tender.id,
            'type': 'ir.actions.act_window',
        }