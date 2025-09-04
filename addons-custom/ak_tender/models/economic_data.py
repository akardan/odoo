# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AkTenderEconomicData(models.Model):
    _name = 'ak.tender.economic.data'
    _description = _('İhale Ekonomik Veriler')
    
    name = fields.Char(string=_('Tanım'), required=True)
    active = fields.Boolean(string=_('Aktif'), default=True)
    
    # Para Birimi İlişkisi
    currency_id = fields.Many2one(
        'res.currency',
        string=_('Para Birimi'),
        required=True,
        default=lambda self: self.env.company.currency_id,
        help=_("Bu ekonomik verilerin geçerli olduğu para birimi.")
    )
    
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
        ('name_currency_uniq', 'unique(name, currency_id, company_id)', _('Bu para birimi için bu tanım zaten mevcut!'))
    ]
    
    @api.model
    def get_default_npv_rate(self, currency_id=None):
        """
        Varsayılan NPV oranını döndürür.
        Aktif ve geçerli bir ekonomik veri kaydı varsa onun NPV oranını,
        yoksa varsayılan değeri (10.0) döndürür.
        
        :param currency_id: Para birimi ID'si
        :return: NPV oranı
        """
        today = fields.Date.context_today(self)
        
        # Use a simpler domain to ensure we find records
        domain = [
            ('active', '=', True)
        ]
        
        # Para birimi belirtilmişse, o para birimine özgü verileri ara
        if currency_id:
            domain.append(('currency_id', '=', currency_id))
        
        # Perform the search
        economic_data = self.search(domain, limit=1, order='date_from desc')
        
        if economic_data:
            return economic_data.npv_rate
        
        # Belirtilen para birimi için veri bulunamazsa, şirket para birimi için ara
        if currency_id and currency_id != self.env.company.currency_id.id:
            return self.get_default_npv_rate(self.env.company.currency_id.id)
        
        # Hiçbir veri bulunamazsa varsayılan değeri döndür
        return 10.0
    
    @api.model
    def get_economic_data_for_currency(self, currency_id):
        """
        Belirli bir para birimi için ekonomik verileri döndürür.
        
        :param currency_id: Para birimi ID'si
        :return: Ekonomik veriler sözlüğü
        """
        today = fields.Date.context_today(self)
        
        # Use a simpler domain to ensure we find records
        domain = [
            ('active', '=', True)
        ]
        
        # Para birimi belirtilmişse, o para birimine özgü verileri ara
        if currency_id:
            domain.append(('currency_id', '=', currency_id))
        
        # Perform the search
        economic_data = self.search(domain, limit=1, order='date_from desc')
        
        if economic_data:
            return {
                'npv_rate': economic_data.npv_rate,
                'inflation_rate': economic_data.inflation_rate,
                'interest_rate': economic_data.interest_rate,
                'currency_id': economic_data.currency_id.id,
                'currency_name': economic_data.currency_id.name
            }
        
        # Belirtilen para birimi için veri bulunamazsa, şirket para birimi için ara
        if currency_id and currency_id != self.env.company.currency_id.id:
            return self.get_economic_data_for_currency(self.env.company.currency_id.id)
        
        # Hiçbir veri bulunamazsa varsayılan değerleri döndür
        return {
            'npv_rate': 10.0,
            'inflation_rate': 0.0,
            'interest_rate': 0.0,
            'currency_id': self.env.company.currency_id.id,
            'currency_name': self.env.company.currency_id.name
        }