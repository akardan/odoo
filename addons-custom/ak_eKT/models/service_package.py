from odoo import models, fields, api

class ServicePackage(models.Model):
    _name = 'digital.service.package'
    _description = 'Hizmet Paketleri'

    name = fields.Char(string='Paket Adı', required=True)
    code = fields.Char(string='Paket Kodu', required=True)  # S, M, L, XL
    max_prospectus = fields.Integer(string='Maksimum Prospektüs Sayısı')
    price = fields.Float(string='Fiyat')
    currency_id = fields.Many2one('res.currency', string='Para Birimi', 
                                 default=lambda self: self.env.company.currency_id.id)
    
    # Özellikler
    ai_voice_included = fields.Boolean(string='AI Seslendirme Dahil', default=False)
    studio_voice_included = fields.Boolean(string='Stüdyo Seslendirme Dahil', default=False)
    multi_language = fields.Boolean(string='Çoklu Dil Desteği', default=False)
    custom_development = fields.Boolean(string='Özel Yazılım Geliştirme', default=False)
    account_manager = fields.Boolean(string='Müşteri Hesap Yöneticisi', default=False)
    
    # Paket açıklaması
    description = fields.Html(string='Açıklama')
    
    active = fields.Boolean(string='Aktif', default=True)
    
    # Abonelikler
    subscription_ids = fields.One2many(
        'digital.customer.subscription',
        'package_id',
        string='Abonelikler'
    )
    
    subscription_count = fields.Integer(
        string='Abonelik Sayısı',
        compute='_compute_subscription_count'
    )
    
    @api.depends('subscription_ids')
    def _compute_subscription_count(self):
        for record in self:
            record.subscription_count = len(record.subscription_ids)
    
    def action_view_subscriptions(self):
        self.ensure_one()
        return {
            'name': 'Abonelikler',
            'type': 'ir.actions.act_window',
            'res_model': 'digital.customer.subscription',
            'view_mode': 'tree,form',
            'domain': [('package_id', '=', self.id)],
            'context': {'default_package_id': self.id}
        }