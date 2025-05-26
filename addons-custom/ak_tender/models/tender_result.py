# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AkTenderResult(models.Model):
    _name = 'ak.tender.result'
    _description = 'İhale Teklif Sonucu'
    _order = 'total_price asc, offer_date desc' # En düşük fiyata ve en yeni tarihe göre sırala

    tender_id = fields.Many2one('ak.tender', string='İhale', required=True, ondelete='cascade')
    
    
    @api.depends('tender_id', 'tender_id.invited_partners')
    def _compute_partner_domain(self):
        for record in self:
            import json
            if record.tender_id and record.tender_id.invited_partners:
                record.partner_domain = json.dumps([('id', 'in', record.tender_id.invited_partners.ids)])
            else:
                record.partner_domain = json.dumps([('supplier_rank', '>=', 0)])
    
    partner_domain = fields.Char(compute='_compute_partner_domain', store=False)
    partner_id = fields.Many2one('res.partner', string='Tedarikçi', required=True,
                                 domain="partner_domain",
                                 help="Teklifi veren tedarikçi.")
    
    offer_date = fields.Datetime(string='Teklif Tarihi', default=fields.Datetime.now(), readonly=True)
    
    # TEKLİF DOKÜMANINA GÖRE YENİ ALAN: HANGİ TUR TEKLİFİ
    tender_round = fields.Selection([
        ('first', '1. Tur Teklif'),
        ('second', '2. Tur Teklif (Revizyon)'),
        ('other', 'Diğer'), # İhtiyaç duyulursa
    ], string='Teklif Turu', default='first', required=True,
    help="Bu teklifin hangi turda sunulduğu.")
    
    currency_id = fields.Many2one('res.currency', string='Para Birimi', required=True,
                                 default=lambda self: self.env.company.currency_id)
    
    # Teklif kalemleri - her bir ihale kalemi için ayrı fiyat
    result_lines = fields.One2many('ak.tender.result.line', 'result_id', string='Teklif Kalemleri')
    
    total_price = fields.Monetary(string='Toplam Teklif Fiyatı', compute='_compute_total_price', store=True, currency_field='currency_id',
                                  help="Tüm kalemler için toplam teklif fiyatı.")
    
    delivery_date = fields.Date(string='Tedarikçi Teslim Tarihi', help="Tedarikçinin taahhüt ettiği teslim tarihi.")
    payment_terms = fields.Many2one('account.payment.term', string='Ödeme Koşulları', help="Tedarikçinin teklif ettiği ödeme koşulları.")
    guarantee_period = fields.Char(string='Garanti Süresi', help="Tedarikçinin sunduğu garanti süresi (örn: 2 Yıl).")
    notes = fields.Text(string='Tedarikçinin Notları', help="Tedarikçinin ek notları veya teklif detayları.")
    
    status = fields.Selection([
        ('received', 'Alındı'),
        ('rejected', 'Reddedildi'),
        ('selected', 'Seçildi'), # Kazanan teklifi işaretlemek için
    ], string='Teklif Durumu', default='received', tracking=True)

    purchase_order_id = fields.Many2one('purchase.order', string='Oluşturulan SAS', readonly=True, copy=False,
                                        help="Bu teklif sonucunda oluşturulan Satın Alma Siparişi.")
    
    @api.depends('result_lines.price_subtotal')
    def _compute_total_price(self):
        for record in self:
            record.total_price = sum(line.price_subtotal for line in record.result_lines)

    # Method to create result lines for all tender lines when a new result is created
    @api.model
    def create(self, vals):
        result = super(AkTenderResult, self).create(vals)
        # Create result lines for each tender line
        if result.tender_id:
            result._create_missing_result_lines()
        return result
    
    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        """When tender_id changes, create missing result lines"""
        if self.tender_id:
            # Clear existing result lines if tender_id changes to avoid inconsistencies
            # The actual creation of result lines will be handled by the create method
            # or the 'create_missing_result_lines' button after the record is saved.
            self.result_lines = [(5, 0, 0)] # This clears all existing lines
    
    def create_missing_result_lines(self):
        """Public method to create missing result lines, callable from a button"""
        return self._create_missing_result_lines()
        
    def _create_missing_result_lines(self):
        """Create result lines for any missing tender lines"""
        self.ensure_one()
        if not self.tender_id or not self.tender_id.tender_lines:
            if self._context.get('from_button'):
                raise ValidationError(_('İhale kalemleri bulunamadı.'))
            return
            
        # Get existing tender_line_ids in result_lines
        existing_tender_line_ids = self.result_lines.mapped('tender_line_id.id')
        
        # Create result lines for any missing tender lines
        created_count = 0
        for tender_line in self.tender_id.tender_lines:
            if tender_line.id not in existing_tender_line_ids:
                self.env['ak.tender.result.line'].create({
                    'result_id': self.id,
                    'tender_line_id': tender_line.id,
                    'price_unit': 0.0,  # Default price
                })
                created_count += 1
        
        if self._context.get('from_button'):
            if created_count:
                raise ValidationError(_('%d adet eksik kalem oluşturuldu.') % created_count)
            else:
                raise ValidationError(_('Tüm kalemler zaten mevcut.'))
        
    
