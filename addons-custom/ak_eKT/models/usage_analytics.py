from odoo import models, fields, api

class ProspectusUsageAnalytics(models.Model):
    _name = 'prospectus.usage.analytics'
    _description = 'Prospektüs Kullanım Analitiği'
    _order = 'access_date desc'

    prospectus_id = fields.Many2one(
        'digital.prospectus',
        string='Prospektüs',
        required=True,
        ondelete='cascade'
    )
    
    action = fields.Selection([
        ('view', 'Görüntülenme'),
        ('download', 'İndirme'),
        ('audio_play', 'Ses Oynatma'),
        ('language_change', 'Dil Değişikliği')
    ], string='Eylem', required=True)
    
    access_date = fields.Datetime(
        string='Erişim Tarihi', 
        required=True,
        default=fields.Datetime.now
    )
    
    user_ip = fields.Char(string='IP Adresi')
    user_agent = fields.Text(string='Tarayıcı Bilgisi')
    language = fields.Char(string='Dil')
    
    # Coğrafi bilgi (isteğe bağlı)
    country_code = fields.Char(string='Ülke Kodu')
    city = fields.Char(string='Şehir')
    
    # İlişkiler
    partner_id = fields.Many2one(
        related='prospectus_id.partner_id',
        store=True,
        string='İlaç Firması'
    )
    
    product_id = fields.Many2one(
        related='prospectus_id.product_id',
        store=True,
        string='Ürün'
    )
    
    # İstatistikler için yardımcı alanlar
    month = fields.Char(
        string='Ay',
        compute='_compute_date_fields',
        store=True
    )
    
    week = fields.Char(
        string='Hafta',
        compute='_compute_date_fields',
        store=True
    )
    
    day = fields.Date(
        string='Gün',
        compute='_compute_date_fields',
        store=True
    )
    
    @api.depends('access_date')
    def _compute_date_fields(self):
        for record in self:
            if record.access_date:
                record.month = record.access_date.strftime('%Y-%m')
                record.week = record.access_date.strftime('%Y-W%W')
                record.day = record.access_date.date()
            else:
                record.month = False
                record.week = False
                record.day = False