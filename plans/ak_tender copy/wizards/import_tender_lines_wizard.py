# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MoveTenderLinesWizard(models.TransientModel):
    _name = 'ak.tender.move.lines.wizard'
    _description = 'Move Tender Lines to New Tender'

    # Fields for new tender creation
    name = fields.Char(string=_('Yeni İhale Adı'), required=True)
    tender_type = fields.Selection([
        ('direct', _('Direkt İhale')),
        ('indirect', _('Endirekt İhale')),
        # ('purchase', _('Satınalma İhalesi')),
        # ('service', _('Hizmet İhalesi')),
        ('mice', _('MICE İhalesi')),
        ('promotion', _('Promosyon İhalesi')),
        # ('other', _('Diğer')),
    ], string=_('İhale Tipi'), required=True, default='purchase')
    
    buyer_id = fields.Many2one(
        'res.users',
        string=_('Satın Alma Uzmanı'),
        required=True,
        help=_("Yeni ihaleyi yönetecek satın alma uzmanı.")
    )
    
    start_date = fields.Datetime(string=_('Başlangıç Tarihi'), required=True)
    end_date = fields.Datetime(string=_('Bitiş Tarihi'), required=True)
    
    request_date = fields.Date(string=_('Talep Tarihi'),
                               help=_("SAT'ın talep edildiği tarih."))
    
    required_delivery_date = fields.Date(string=_('Gerekli Teslim Tarihi'),
                                         help=_("İstenen teslimat tarihi."))
    
    original_tender_id = fields.Many2one('ak.tender', string=_('Orijinal İhale'), readonly=True)
    
    tender_line_ids = fields.Many2many(
        'ak.tender.line',
        string=_('Taşınacak İhale Kalemleri'),
        required=True,
        domain="[('tender_id', '=', original_tender_id)]"
    )

    @api.model
    def default_get(self, fields):
        res = super(MoveTenderLinesWizard, self).default_get(fields)
        
        # Get active ID from context (selected tender)
        active_id = self.env.context.get('active_id')
        if active_id:
            original_tender = self.env['ak.tender'].browse(active_id)
            res['original_tender_id'] = original_tender.id
            
            # Try to infer a default name based on the original tender name and sequence
            if 'name' in fields:
                original_tender_name = original_tender.name
                
                # Count existing tenders starting with the original name
                name_search_domain = [('name', 'ilike', original_tender_name + '%')]
                existing_tenders_count = self.env['ak.tender'].search_count(name_search_domain)
                
                # Determine the sequence number (if count is 0, it's 1, otherwise count + 1)
                sequence_number = existing_tenders_count + 1
                
                res['name'] = f"{original_tender_name}-{sequence_number}"
                
            # Copy required dates
            if 'start_date' in fields and original_tender.start_date:
                res['start_date'] = original_tender.start_date
            if 'end_date' in fields and original_tender.end_date:
                res['end_date'] = original_tender.end_date
            
            # Copy request date
            if 'request_date' in fields and original_tender.request_date:
                res['request_date'] = original_tender.request_date
                
            # Copy required delivery date
            if 'required_delivery_date' in fields and original_tender.required_delivery_date:
                res['required_delivery_date'] = original_tender.required_delivery_date
                
            # Try to infer default tender type
            if 'tender_type' in fields and original_tender.tender_type:
                res['tender_type'] = original_tender.tender_type
                
            # Try to infer default buyer (res.users) from the original tender
            if 'buyer_id' in fields:
                # Use the original tender's buyer_id as default
                res['buyer_id'] = original_tender.buyer_id.id if original_tender.buyer_id else self.env.user.id
                
            # Pre-select all lines from the original tender
            if 'tender_line_ids' in fields:
                res['tender_line_ids'] = [(6, 0, original_tender.tender_lines.ids)]
                    
        return res

    def action_move_lines(self):
        self.ensure_one()
        
        if not self.tender_line_ids:
            raise UserError(_("Taşınacak ihale kalemi seçilmedi."))

        original_tender = self.original_tender_id
        
        # Find the initial state of the copied workflow definition
        initial_state = original_tender.workflow_definition_id.state_ids.filtered(lambda s: s.is_initial)
        
        # 1. Create the new tender record
        new_tender_vals = {
            'name': self.name,
            'workflow_current_state_id': initial_state[0].id if initial_state else False,
            'tender_type': self.tender_type,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'request_date': self.request_date,
            'required_delivery_date': self.required_delivery_date,
            'buyer_id': self.buyer_id.id,
            
            # Copy other relevant fields from the original tender
            'tender_round': 1,  # New tender starts at round 1
            'erp_pr_id': original_tender.erp_pr_id,
            'erp_company_code': original_tender.erp_company_code,
            'erp_plant_code': original_tender.erp_plant_code,
            'erp_requester': original_tender.erp_requester,
            'currency_id': original_tender.currency_id.id,
            'workflow_definition_id': original_tender.workflow_definition_id.id,
            'description': original_tender.description,
            'location_dest_id': original_tender.location_dest_id.id,
            # Note: We don't copy invited_partners or purchase_order_ids
        }
            
        new_tender = self.env['ak.tender'].create(new_tender_vals)

        # 2. Move the selected tender lines to the new tender
        # We only update the tender_id field.
        self.tender_line_ids.write({
            'tender_id': new_tender.id,
        })

        # 3. Return an action to open the newly created tender
        return {
            'name': _('Yeni İhale: %s') % new_tender.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender',
            'res_id': new_tender.id,
            'view_mode': 'form',
            'target': 'current',
        }