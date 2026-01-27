# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TenderTemplateSelectionWizard(models.TransientModel):
    _name = 'ak.tender.template.selection.wizard'
    _description = _('İhale Şablonu Seçim Sihirbazı')

    tender_id = fields.Many2one('ak.tender', string=_('İhale'), required=True)
    tender_type = fields.Selection(related='tender_id.tender_type', readonly=True)
    template_id = fields.Many2one(
        'ak.tender.template', 
        string=_('Şablon'), 
        required=True,
        domain="[('tender_type', '=', tender_type), ('active', '=', True)]"
    )
    
    def action_apply_template(self):
        """Apply the selected template to the tender."""
        self.ensure_one()
        if not self.template_id:
            raise ValidationError(_("Lütfen bir şablon seçin."))
        
        # Apply the template to the tender
        self.tender_id.apply_template_items(self.template_id)
        
        return {'type': 'ir.actions.act_window_close'}