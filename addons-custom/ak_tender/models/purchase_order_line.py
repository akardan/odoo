# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Fields from ak.tender.result.line
    # 'result_id' is now 'order_id' which is already on the model.
    
    tender_line_id = fields.Many2one('ak.tender.line', string='İhale Kalemi', ondelete='set null')
    
    # Otel seçimi için
    hotel_partner_id = fields.Many2one(
        'res.partner',
        string=_("Otel"),
        domain=[('is_hotel', '=', True)],
        help=_("Konaklama için otel seçin")
    )
    
    # Multi-currency support
    currency_id = fields.Many2one('res.currency', string='Para Birimi',
                                 help="Teklif kaleminin para birimi. Farklı para birimlerinde teklif verebilmek için kullanılır.",
                                 default=lambda self: self.env.company.currency_id)
    
    # Alternative product support is handled by alt_materials field
    
    # Additional fields for supplier portal editing
    warranty_period = fields.Integer(
        string='Garanti Süresi (Ay)',
        help='Tedarikçi tarafından sunulan garanti süresi (ay olarak)'
    )
    
    supplier_ref = fields.Char(
        string='Tedarikçi Referansı',
        help='Bu ürün için tedarikçinin referans veya parça numarası'
    )
    
    alt_materials = fields.Text(
        string='Alternatif Malzemeler',
        help='Tedarikçi tarafından önerilen alternatif malzemeler veya ürünler'
    )
    
    # NPV calculation fields
    discount_rate = fields.Float(
        string='İskonto Oranı (%)',
        default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('ak_tender_npv_interest_rate', '10.0')),
        help="İhale sürecinde kullanılacak iskonto oranı."
    )
    npv_value = fields.Monetary(
        string='NPV Değeri',
        currency_field='currency_id',
        help="Net Bugünkü Değer hesaplaması sonucu.",
        readonly=True
    )
    
    # The following fields are already on purchase.order.line, but we are adding them
    # to show the link and in case any properties needed to be modified.
    # product_id, name, product_qty (quantity), product_uom (uom_id) are standard fields.
    
    # We can ensure that the description and UoM are linked to the tender line if it exists.
    @api.onchange('tender_line_id')
    def _onchange_tender_line_id(self):
        """Update line fields based on tender line"""
        if not self.tender_line_id:
            return
            
        self.name = self.tender_line_id.name or ''
        self.product_uom = self.tender_line_id.uom_id.id if self.tender_line_id.uom_id else (self.product_id.uom_id.id if self.product_id else False)
        self.product_qty = self.tender_line_id.quantity or 1.0
        
        # Otel bilgilerini kopyala
        if self.tender_line_id.product_id and self.tender_line_id.product_id.is_hotel_accommodation:
            self.hotel_partner_id = self.tender_line_id.hotel_partner_id
            
            # Oda-pansiyon bilgisini name sonuna ekle
            if self.tender_line_id.uom_id and self.tender_line_id.uom_id.name:
                self.name = f"{self.name} - {self.tender_line_id.uom_id.name}"

    # price_unit is a standard field.
    # price_subtotal is a standard field.
    
    # The logic in _compute_price_subtotal is already standard in purchase.order.line
    # No need to re-implement it unless the logic is different.
    # The original model had a simple multiplication, which is the default behavior.
    
    def calculate_npv(self):
        """
        Calculate Net Present Value (NPV) based on the line amount, NPV rate (inflation rate), and payment term.
        
        NPV = Amount / (1 + (npv_rate/100)/365)^payment_term_days
        
        This uses the inflation rate from the tender to calculate the present value of future payments.
        """
        for line in self:
            # Get the line amount
            amount = line.price_subtotal or 0.0
            
            # Import logging at the beginning of the method
            import logging
            _logger = logging.getLogger(__name__)
            
            # Get payment term days
            payment_term_days = 30  # Default to 30 days if no payment term is defined
            if line.order_id and line.order_id.payment_term_id:
                _logger.info('Payment term found: %s', line.order_id.payment_term_id.name)
                if line.order_id.payment_term_id.line_ids:
                    # İlk ödeme koşulu satırını kullan
                    term_line = line.order_id.payment_term_id.line_ids[0]
                    _logger.info('Payment term line: value=%s, nb_days=%s', term_line.value, term_line.nb_days)
                    payment_term_days = term_line.nb_days
                    _logger.info('Using payment term days: %s', payment_term_days)
                else:
                    _logger.warning('Payment term has no lines: %s', line.order_id.payment_term_id.name)
            else:
                _logger.info('No payment term defined, using default: %s days', payment_term_days)
            
            # Get NPV rate from tender
            npv_rate = 10.0  # Default value
            if line.order_id and line.order_id.tender_id:
                # İhale üzerindeki NPV oranını kullan
                npv_rate = line.order_id.tender_id.npv_rate or 10.0
                _logger.info('Using tender NPV rate: %s', npv_rate)
            
            # If no amount to calculate, set NPV to zero
            if not amount:
                line.npv_value = 0.0
                continue
                
            # Ensure npv_rate is not zero to avoid division by zero
            if npv_rate <= 0:
                _logger.warning('NPV rate is zero or negative, using default value 0.1')
                npv_rate = 0.1  # Use a small positive value instead of zero
                
            # Log calculation parameters for debugging
            _logger.info('NPV Calculation - Line: %s, Amount: %s, NPV Rate: %s, Payment Term Days: %s',
                        line.name, amount, npv_rate, payment_term_days)
            
            # Calculate NPV using inflation rate (npv_rate)
            daily_rate = (npv_rate / 100) / 365
            npv_value = amount / ((1 + daily_rate) ** payment_term_days)
            line.npv_value = npv_value
            
            # Log calculation details
            _logger.info('NPV Calculation Details - Daily Rate: %s, Formula: %s / ((1 + %s) ^ %s) = %s',
                        daily_rate, amount, daily_rate, payment_term_days, npv_value)
        
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
