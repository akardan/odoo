# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AkTenderResultLine(models.Model):
    _name = 'ak.tender.result.line'
    _description = 'İhale Teklif Sonuç Kalemi'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sıra', default=10)
    result_id = fields.Many2one('ak.tender.result', string='Teklif Sonucu', required=True, ondelete='cascade')
    tender_line_id = fields.Many2one('ak.tender.line', string='İhale Kalemi', required=True,
                                    domain="[('tender_id', '=', parent_tender_id)]")
    parent_tender_id = fields.Many2one('ak.tender', related='result_id.tender_id', 
                                      string='İlgili İhale', store=True)
    
    product_id = fields.Many2one('product.product', related='tender_line_id.product_id', 
                                string='Ürün/Malzeme', readonly=True, store=True)
    name = fields.Char(string='Açıklama', related='tender_line_id.name', readonly=True)
    quantity = fields.Float(string='Miktar', related='tender_line_id.quantity', readonly=True)
    uom_id = fields.Many2one('uom.uom', string='Birim', related='tender_line_id.uom_id', readonly=True)
    
    currency_id = fields.Many2one('res.currency', related='result_id.currency_id', 
                                 string='Para Birimi', readonly=True, store=True)
    price_unit = fields.Monetary(string='Birim Fiyatı', currency_field='currency_id', required=True,
                                help="Tedarikçinin bu kalem için teklif ettiği birim fiyat.")
    price_subtotal = fields.Monetary(string='Ara Toplam', compute='_compute_price_subtotal', 
                                    store=True, currency_field='currency_id')
    
    @api.depends('price_unit', 'quantity')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.quantity
    
    # @api.constrains('price_unit')
    # def _check_positive_price(self):
    #     for record in self:
    #         if record.price_unit <= 0:
    #             raise ValidationError(_("Birim Fiyatı sıfırdan büyük olmalıdır."))