from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class CustomerSubscription(models.Model):
    _name = 'digital.customer.subscription'
    _description = 'Müşteri Aboneliği'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'

    name = fields.Char(
        string='Abonelik Adı',
        compute='_compute_name',
        store=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Müşteri',
        required=True,
        tracking=True
    )
    
    package_id = fields.Many2one(
        'digital.service.package',
        string='Hizmet Paketi',
        required=True,
        tracking=True
    )
    
    start_date = fields.Date(
        string='Başlangıç Tarihi', 
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    end_date = fields.Date(
        string='Bitiş Tarihi', 
        required=True,
        tracking=True
    )
    
    prospectus_count = fields.Integer(
        string='Mevcut Prospektüs Sayısı',
        compute='_compute_prospectus_count'
    )
    
    remaining_quota = fields.Integer(
        string='Kalan Kota',
        compute='_compute_remaining_quota'
    )
    
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('active', 'Aktif'),
        ('expired', 'Süresi Dolmuş'),
        ('cancelled', 'İptal')
    ], string='Durum', default='draft', tracking=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Şirket',
        default=lambda self: self.env.company
    )
    
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Para Birimi'
    )
    
    price = fields.Monetary(
        string='Fiyat',
        related='package_id.price',
        readonly=True
    )
    
    notes = fields.Text(string='Notlar')
    
    @api.depends('partner_id', 'package_id', 'start_date')
    def _compute_name(self):
        for record in self:
            if record.partner_id and record.package_id and record.start_date:
                record.name = f"{record.partner_id.name} - {record.package_id.name} - {record.start_date.strftime('%d/%m/%Y')}"
            else:
                record.name = _("Yeni Abonelik")
    
    @api.depends('partner_id')
    def _compute_prospectus_count(self):
        for record in self:
            record.prospectus_count = self.env['digital.prospectus'].search_count([
                ('partner_id', '=', record.partner_id.id),
                ('state', 'in', ['approved', 'published'])
            ])
    
    @api.depends('prospectus_count', 'package_id.max_prospectus')
    def _compute_remaining_quota(self):
        for record in self:
            if record.package_id:
                record.remaining_quota = record.package_id.max_prospectus - record.prospectus_count
            else:
                record.remaining_quota = 0
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("Bitiş tarihi başlangıç tarihinden önce olamaz!"))
    
    @api.model
    def create(self, vals):
        res = super(CustomerSubscription, self).create(vals)
        # Abonelik oluşturulduğunda otomatik olarak aktif yap
        if res.state == 'draft':
            res.state = 'active'
        return res
    
    def action_activate(self):
        self.state = 'active'
        self.message_post(body=_("Abonelik aktifleştirildi."))
    
    def action_cancel(self):
        self.state = 'cancelled'
        self.message_post(body=_("Abonelik iptal edildi."))
    
    def action_view_prospectus(self):
        self.ensure_one()
        return {
            'name': _('Prospektüsler'),
            'type': 'ir.actions.act_window',
            'res_model': 'digital.prospectus',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id}
        }
    
    @api.model
    def _cron_check_expired_subscriptions(self):
        """Süresi dolan abonelikleri kontrol et"""
        today = fields.Date.today()
        expired_subscriptions = self.search([
            ('end_date', '<', today),
            ('state', '=', 'active')
        ])
        
        for subscription in expired_subscriptions:
            subscription.state = 'expired'
            subscription.message_post(
                body=_('Abonelik süresi doldu ve otomatik olarak pasif duruma alındı.')
            )