# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Fields from ak.tender.result
    tender_id = fields.Many2one('ak.tender', string='İhale', ondelete='restrict')
    
    # The domain for partner_id will be handled in the view to ensure correctness.

    offer_date = fields.Datetime(string='Teklif Tarihi', default=fields.Datetime.now, readonly=True)
    tender_round = fields.Integer(string='Teklif Turu', default=1, help="Bu teklifin hangi turda sunulduğu (1, 2, 3...).")
    
    # currency_id is already in purchase.order
    
    # result_lines are now order_line
    # total_price is amount_total in purchase.order

    delivery_date = fields.Date(string='Teslim Tarihi', help="Tedarikçinin taahhüt ettiği teslim tarihi.")
    # payment_terms_id is already in purchase.order
    guarantee_period = fields.Char(string='Garanti Süresi', help="Tedarikçinin sunduğu garanti süresi (örn: 2 Yıl).")
    # notes is notes in purchase.order
    
    # status is state in purchase.order. We might need to map these.
    tender_offer_status = fields.Selection([
        ('received', 'Alındı'),
        ('rejected', 'Reddedildi'),
        ('selected', 'Seçildi'),
    ], string='Teklif Durumu', default='received', tracking=True)

    # purchase_order_id is self.id now.
    
    is_readonly = fields.Boolean(compute='_compute_is_readonly', store=False)

    @api.depends('tender_id.workflow_current_state_id', 'tender_round')
    def _compute_is_readonly(self):
        for record in self:
            record.is_readonly = False
            if not record.tender_id:
                continue
            state_code = record.tender_id.workflow_current_state_id.code if record.tender_id.workflow_current_state_id else None
            if state_code == 'second_tender_round' and record.tender_round == 1:
                record.is_readonly = True

    # The logic for creating lines needs to be adapted.
    # The original logic was creating 'ak.tender.result.line' for each 'ak.tender.line'.
    # Now we need to create 'purchase.order.line' for each 'ak.tender.line'.
    def create_lines_from_tender(self):
        self.ensure_one()
        if not self.tender_id or not self.tender_id.tender_lines:
            return

        # Clear existing lines to avoid duplicates if re-run
        self.order_line = [(5, 0, 0)]
        
        lines_to_create = []
        for tender_line in self.tender_id.tender_lines:
            lines_to_create.append((0, 0, {
                'product_id': tender_line.product_id.id,
                'name': tender_line.name,
                'product_qty': tender_line.quantity,
                'product_uom': tender_line.uom_id.id,
                'price_unit': 0, # Price will be filled by the supplier
                'date_planned': self.date_planned or fields.Date.today(),
                # Link back to the tender line
                'tender_line_id': tender_line.id,
            }))
        
        self.order_line = lines_to_create

    @api.model
    def create(self, vals):
        # If a tender_id is provided, we might want to auto-create lines
        order = super(PurchaseOrder, self).create(vals)
        if order.tender_id:
            order.create_lines_from_tender()
        return order
