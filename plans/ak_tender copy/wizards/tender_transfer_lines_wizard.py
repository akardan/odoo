# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TenderTransferLinesWizard(models.TransientModel):
    _name = 'ak.tender.transfer.lines.wizard'
    _description = _('İhaleden Kalem Aktarma Sihirbazı')

    tender_id = fields.Many2one('ak.tender', string=_('Hedef İhale'), required=True, readonly=True)
    source_tender_id = fields.Many2one(
        'ak.tender', 
        string=_('Kaynak İhale'), 
        required=True,
        domain="[('id', '!=', tender_id)]",
        help=_("Kalemleri aktarmak istediğiniz ihale")
    )
    tender_line_ids = fields.Many2many(
        'ak.tender.line',
        string=_('Aktarılacak Kalemler'),
        domain="[('tender_id', '=', source_tender_id), ('display_type', '=', False)]",
        help=_("Aktarmak istediğiniz ihale kalemlerini seçin")
    )
    
    @api.onchange('source_tender_id')
    def _onchange_source_tender_id(self):
        """Kaynak ihale değiştiğinde seçili kalemleri temizle"""
        if self.source_tender_id:
            self.tender_line_ids = [(5, 0, 0)]
    
    def action_transfer_lines(self):
        """Transfer selected lines from source tender to target tender."""
        self.ensure_one()
        
        if not self.source_tender_id:
            raise ValidationError(_("Lütfen kaynak ihale seçin."))
        
        if not self.tender_line_ids:
            raise ValidationError(_("Lütfen aktarmak istediğiniz kalemleri seçin."))
        
        # Transfer lines to the target tender
        transferred_count = self.tender_id.transfer_lines_from_tender(self.tender_line_ids)
        
        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İşlem Başarılı'),
                'message': _('%s kalem başarıyla aktarıldı.') % transferred_count,
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
