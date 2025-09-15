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
    
    discount_rate = fields.Float(
        string='İskonto Oranı (%)',
        default=0.0,
        help="İhale sürecinde kullanılacak iskonto oranı."
    )

    # NPV calculation fields
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
        
        For split payment terms, calculates NPV for each term separately and sums them:
        NPV = Sum[ (Amount * term_percent) / (1 + (npv_rate/100)/365)^term_days ]
        
        This uses the inflation rate from the tender to calculate the present value of future payments.
        """
        for line in self:
            # Skip section and note lines
            if line.display_type in ('line_section', 'line_note'):
                line.npv_value = 0.0
                continue
                
            # Get the line amount
            amount = line.price_subtotal or 0.0
            
            # If no amount to calculate, set NPV to zero
            if not amount:
                line.npv_value = 0.0
                continue
            
            # Get NPV rate from tender
            npv_rate = 10.0  # Default value
            if line.order_id and line.order_id.tender_id:
                # İhale üzerindeki NPV oranını kullan
                npv_rate = line.order_id.tender_id.npv_rate or 10.0
                
            # Ensure npv_rate is not zero to avoid division by zero
            if npv_rate <= 0:
                npv_rate = 0.1  # Use a small positive value instead of zero
            
            daily_rate = (npv_rate / 100) / 365
            
            # Calculate NPV based on payment terms
            npv_value = 0.0
            
            # Check if payment term exists and has lines
            if line.order_id and line.order_id.payment_term_id and line.order_id.payment_term_id.line_ids:
                payment_term_lines = line.order_id.payment_term_id.line_ids
                
                # If there are multiple payment term lines, calculate NPV for each one
                for term_line in payment_term_lines:
                    # Get days for this term line
                    term_days = term_line.nb_days or 0
                    
                    # Calculate value percentage based on value and value_amount
                    # According to account.payment.term.line model structure
                    if term_line.value == 'percent':
                        term_percent = term_line.value_amount / 100.0
                    elif term_line.value == 'fixed':
                        # For fixed amount, calculate percentage of total
                        total_amount = line.order_id.amount_total
                        term_percent = term_line.value_amount / total_amount if total_amount else 0
                    else:
                        # Default to equal distribution if we can't determine the percentage
                        term_percent = 1.0 / len(payment_term_lines)
                    
                    # Calculate NPV for this term portion
                    term_amount = amount * term_percent
                    term_npv = term_amount / ((1 + daily_rate) ** term_days)
                    npv_value += term_npv
            else:
                # Default to 30 days if no payment term is defined
                payment_term_days = 30
                npv_value = amount / ((1 + daily_rate) ** payment_term_days)
            
            line.npv_value = npv_value
        
        return True
    
    @api.model
    def create(self, vals):
        # Check if this is a section or note line
        is_non_accountable = vals.get('display_type') in ('line_section', 'line_note')
        
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
        
        # For non-accountable lines (section/note), set special values
        if is_non_accountable:
            vals.update({
                'product_id': False,
                'product_qty': 0.0,
                'product_uom': False,
                'price_unit': 0.0,
            })
        else:
            # For regular product lines, ensure required fields are set
            # Ensure product_qty is set (required field)
            if 'product_qty' not in vals or not vals.get('product_qty'):
                vals['product_qty'] = 1.0
                
            # Ensure product_uom is set (required field)
            if 'product_uom' not in vals or not vals.get('product_uom'):
                # Find a default UOM
                default_uom = self.env['uom.uom'].search([], limit=1)
                vals['product_uom'] = default_uom.id
                
            # Ensure price_unit is set (required field)
            if 'price_unit' not in vals:
                vals['price_unit'] = 0.0
        
        # Ensure date_planned is set (required field)
        if 'date_planned' not in vals:
            vals['date_planned'] = fields.Date.today()
                
        line = super(PurchaseOrderLine, self).create(vals)
        
        # Calculate NPV when creating a line (only for product lines)
        if not is_non_accountable and line.price_subtotal and line.order_id and line.order_id.payment_term_id and line.discount_rate:
            line.calculate_npv()
        
        return line
    
    def write(self, vals):
        # For section and note lines, ensure certain fields are set to NULL/False
        for line in self:
            if line.display_type in ('line_section', 'line_note'):
                # If this is a section or note line, ensure certain fields are NULL
                if 'product_id' in vals and vals['product_id']:
                    vals['product_id'] = False
                if 'product_qty' in vals and vals['product_qty'] != 0.0:
                    vals['product_qty'] = 0.0
                if 'product_uom' in vals and vals['product_uom']:
                    vals['product_uom'] = False
        
        result = super(PurchaseOrderLine, self).write(vals)
        
        # Recalculate NPV when updating relevant fields (only for product lines)
        if any(field in vals for field in ['price_unit', 'product_qty', 'discount_rate']):
            # Only calculate NPV for product lines, not section or note lines
            for line in self:
                if line.display_type not in ('line_section', 'line_note'):
                    line.calculate_npv()
        
        return result
