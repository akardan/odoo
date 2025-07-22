# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Fields from ak.tender.result.line
    # 'result_id' is now 'order_id' which is already on the model.
    
    tender_line_id = fields.Many2one('ak.tender.line', string='İhale Kalemi', ondelete='restrict')
    
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
        if self.tender_line_id:
            self.name = self.tender_line_id.name
            self.product_uom = self.tender_line_id.uom_id.id
            self.product_qty = self.tender_line_id.quantity

    # price_unit is a standard field.
    # price_subtotal is a standard field.
    
    # The logic in _compute_price_subtotal is already standard in purchase.order.line
    # No need to re-implement it unless the logic is different.
    # The original model had a simple multiplication, which is the default behavior.
    
    def calculate_npv(self):
        """
        Calculate Net Present Value (NPV) based on the line amount, discount rate, and payment term.
        
        NPV = Amount / (1 + (discount_rate/100)/365)^payment_term_days
        
        This method calculates the present value of a future payment based on the payment term
        from the purchase order and the annual discount rate.
        """
        self.ensure_one()
        
        # Get the line amount
        amount = self.price_subtotal
        
        # Get payment term days from the purchase order's payment term
        payment_term_days = 0
        if self.order_id.payment_term_id:
            # Get the first line of the payment term (simplified approach)
            for line in self.order_id.payment_term_id.line_ids:
                if line.value == 'balance':
                    payment_term_days = line.days
                    break
        
        # If no amount to calculate or no payment term, set NPV to zero
        if not amount or not payment_term_days or not self.discount_rate:
            self.npv_value = 0.0
            return
        
        # Calculate daily discount rate
        daily_rate = (self.discount_rate / 100) / 365
        
        # Calculate NPV
        npv = amount / ((1 + daily_rate) ** payment_term_days)
        
        # Update the NPV value
        self.npv_value = npv
        
        return npv
    
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
        if line.price_subtotal and line.order_id.payment_term_id and line.discount_rate:
            line.calculate_npv()
        return line
    
    def write(self, vals):
        result = super(PurchaseOrderLine, self).write(vals)
        # Recalculate NPV when updating relevant fields
        if any(field in vals for field in ['price_unit', 'product_qty', 'discount_rate']):
            for line in self:
                line.calculate_npv()
        return result
