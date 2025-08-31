# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AkTenderEconomicData(models.Model):
    _name = 'ak.tender.economic.data'
    _description = _('İhale Ekonomik Veriler')
    
    name = fields.Char(string=_('Tanım'), required=True)
    active = fields.Boolean(string=_('Aktif'), default=True)
    
    # NPV Hesaplama Oranı
    npv_rate = fields.Float(
        string=_('NPV Oranı (%)'), 
        default=10.0,
        required=True,
        help=_("NPV hesaplaması için kullanılacak yıllık oran.")
    )
    
    # Diğer Ekonomik Veriler
    inflation_rate = fields.Float(
        string=_('Enflasyon Oranı (%)'),
        default=0.0,
        help=_("Yıllık enflasyon oranı.")
    )
    
    interest_rate = fields.Float(
        string=_('Faiz Oranı (%)'),
        default=0.0,
        help=_("Yıllık faiz oranı.")
    )
    
    # Veri Kaynağı
    data_source = fields.Selection([
        ('tcmb', _('TCMB')),
        ('tuik', _('TÜİK')),
        ('manual', _('Manuel'))
    ], string=_('Veri Kaynağı'), default='manual',
        help=_("Ekonomik verilerin alındığı kaynak."))
    
    # Geçerlilik Tarihleri
    date_from = fields.Date(
        string=_('Geçerlilik Başlangıç'),
        default=fields.Date.context_today,
        required=True
    )
    
    date_to = fields.Date(
        string=_('Geçerlilik Bitiş'),
        help=_("Boş bırakılırsa süresiz olarak geçerlidir.")
    )
    
    notes = fields.Text(string=_('Notlar'))
    
    company_id = fields.Many2one(
        'res.company', 
        string=_('Şirket'),
        default=lambda self: self.env.company
    )
    
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', _('Bu tanım zaten mevcut!'))
    ]
    
    @api.model
    def get_default_npv_rate(self):
        """
        Varsayılan NPV oranını döndürür.
        Aktif ve geçerli bir ekonomik veri kaydı varsa onun NPV oranını,
        yoksa varsayılan değeri (10.0) döndürür.
        """
        today = fields.Date.context_today(self)
        economic_data = self.search([
            ('active', '=', True),
            ('date_from', '<=', today),
            '|',
            ('date_to', '>=', today),
            ('date_to', '=', False)
        ], limit=1, order='date_from desc')
        
        if economic_data:
            return economic_data.npv_rate
        return 10.0