# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Fields from ak.tender.result.line
    # 'result_id' is now 'order_id' which is already on the model.
    
    tender_line_id = fields.Many2one('ak.tender.line', string='İhale Kalemi', ondelete='restrict')
    
    # The following fields are already on purchase.order.line, but we are adding them
    # to show the link and in case any properties needed to be modified.
    # product_id, name, product_qty (quantity), product_uom (uom_id) are standard fields.
    
    # We can ensure that the description and UoM are linked to the tender line if it exists.
    @api.onchange('tender_line_id')
    def _onchange_tender_line_id(self):
        if self.tender_line_id:
            self.name = self.tender_line_id.name
            self.product_uom = self.tender_line_id.uom_id.id
            self.product_qty = self.tender_line_id.quantity

    # price_unit is a standard field.
    # price_subtotal is a standard field.
    
    # The logic in _compute_price_subtotal is already standard in purchase.order.line
    # No need to re-implement it unless the logic is different.
    # The original model had a simple multiplication, which is the default behavior.
