# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Fields from ak.tender.result.line
    # 'result_id' is now 'order_id' which is already on the model.
    
    tender_line_id = fields.Many2one('ak.tender.line', string='İhale Kalemi', ondelete='set null')
    
    # Multi-currency support
    currency_id = fields.Many2one('res.currency', string='Para Birimi',
                                 help="Teklif kaleminin para birimi. Farklı para birimlerinde teklif verebilmek için kullanılır.",
                                 default=lambda self: self.env.company.currency_id)
    
    # Alternative product support - simplified approach
    alternative_product = fields.Char(string='Muadil Ürün Bilgisi',
                                     help="Eğer teklif edilen ürün talep edilenden farklı ise, "
                                          "muadil ürün bilgilerini buraya giriniz (marka, model, kod vb.).")
    
    # NPV calculation fields
    discount_rate = fields.Float(string='İskonto Oranı (%)',
                                 default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('ak_tender_npv_interest_rate', '10.0')),
                                 help="NPV hesaplaması için kullanılacak yıllık iskonto oranı.")
    npv_value = fields.Monetary(string='NPV Değeri', currency_field='currency_id',
                                help="Net Bugünkü Değer hesaplaması sonucu.", readonly=True)
    
    # The following fields are already on purchase.order.line, but we are adding them
    # to show the link and in case any properties needed to be modified.
    # product_id, name, product_qty (quantity), product_uom (uom_id) are standard fields.
    
    # We can ensure that the description and UoM are linked to the tender line if it exists.
    @api.onchange('tender_line_id')
    def _onchange_tender_line_id(self):
        """Update line fields based on tender line"""
        if self.tender_line_id:
            self.name = self.tender_line_id.name or ''
            self.product_uom = self.tender_line_id.uom_id.id if self.tender_line_id.uom_id else (self.product_id.uom_id.id if self.product_id else False)
            self.product_qty = self.tender_line_id.quantity or 1.0

    # price_unit is a standard field.
    # price_subtotal is a standard field.
    
    # The logic in _compute_price_subtotal is already standard in purchase.order.line
    # No need to re-implement it unless the logic is different.
    # The original model had a simple multiplication, which is the default behavior.
    
    def calculate_npv(self):
        """
        Calculate Net Present Value (NPV) based on the line amount, discount rate, and payment term.
        
        NPV = Amount / (1 + (discount_rate/100)/365)^payment_term_days
        """
        for line in self:
            # Get the line amount
            amount = line.price_subtotal or 0.0
            
            # Get payment term days
            payment_term_days = 0
            if line.order_id and line.order_id.payment_term_id and line.order_id.payment_term_id.line_ids:
                for term_line in line.order_id.payment_term_id.line_ids:
                    if term_line.value == 'balance':
                        payment_term_days = term_line.days
                        break
            
            # If no amount to calculate or no payment term, set NPV to zero
            if not amount or not payment_term_days or not line.discount_rate:
                line.npv_value = 0.0
                continue
            
            # Calculate NPV
            daily_rate = (line.discount_rate / 100) / 365
            line.npv_value = amount / ((1 + daily_rate) ** payment_term_days)
        
        return True
    
    @api.model
    def create(self, vals):
        # Ensure name field is set
        if 'name' not in vals or not vals.get('name'):
            # If product_id is set, use product name as default
            if vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['name'] = product.name or product.display_name or _('Product')
            # If tender_line_id is set, use tender line name as default
            elif vals.get('tender_line_id'):
                tender_line = self.env['ak.tender.line'].browse(vals['tender_line_id'])
                vals['name'] = tender_line.name or _('Tender Line')
            # Otherwise, set a default value
            else:
                vals['name'] = _('Product Description')
                
        line = super(PurchaseOrderLine, self).create(vals)
        
        # Calculate NPV when creating a line
        if line.price_subtotal and line.order_id and line.order_id.payment_term_id and line.discount_rate:
            line.calculate_npv()
        
        return line
    
    def write(self, vals):
        result = super(PurchaseOrderLine, self).write(vals)
        # Recalculate NPV when updating relevant fields
        if any(field in vals for field in ['price_unit', 'product_qty', 'discount_rate']):
            self.calculate_npv()
        return result
