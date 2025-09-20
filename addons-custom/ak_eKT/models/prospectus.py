from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import qrcode
import base64
import io
import uuid
from datetime import datetime, timedelta

class DigitalProspectus(models.Model):
    _name = 'digital.prospectus'
    _description = 'Dijital Prospektüs / e-KT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Prospektüs Adı',
        required=True,
        tracking=True
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='İlaç/Ürün',
        required=True,
        tracking=True
    )
    
    active_ingredient = fields.Text(
        string='Etken Madde',
        help='İlacın etken maddesi'
    )
    
    atc_code = fields.Char(
        string='ATC Kodu',
        help='Anatomical Therapeutic Chemical kodu'
    )
    
    barcode = fields.Char(
        string='Barkod',
        related='product_id.barcode',
        readonly=True,
        store=True
    )
    
    # Prospektüs İçeriği
    content_turkish = fields.Html(
        string='Türkçe İçerik',
        required=True
    )
    
    content_english = fields.Html(
        string='İngilizce İçerik'
    )
    
    content_arabic = fields.Html(
        string='Arapça İçerik'
    )
    
    # Ses Dosyaları
    audio_turkish = fields.Binary(
        string='Türkçe Ses Dosyası',
        help='AI veya stüdyo seslendirme',
        attachment=True
    )
    
    audio_turkish_filename = fields.Char(
        string='Türkçe Ses Dosyası Adı'
    )
    
    audio_english = fields.Binary(
        string='İngilizce Ses Dosyası',
        attachment=True
    )
    
    audio_english_filename = fields.Char(
        string='İngilizce Ses Dosyası Adı'
    )
    
    audio_arabic = fields.Binary(
        string='Arapça Ses Dosyası',
        attachment=True
    )
    
    audio_arabic_filename = fields.Char(
        string='Arapça Ses Dosyası Adı'
    )
    
    # QR Kod ve Erişim
    unique_code = fields.Char(
        string='Benzersiz Kod',
        readonly=True,
        copy=False
    )
    
    qr_code_image = fields.Binary(
        string='QR Kod',
        compute='_compute_qr_code',
        store=True
    )
    
    public_url = fields.Char(
        string='Herkese Açık URL',
        compute='_compute_public_url',
        store=True
    )
    
    # Durum ve Onay
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('review', 'İnceleme'),
        ('approved', 'Onaylı'),
        ('published', 'Yayında'),
        ('expired', 'Süresi Dolmuş'),
        ('cancelled', 'İptal')
    ], string='Durum', default='draft', tracking=True)
    
    # Tarihler
    approval_date = fields.Datetime(string='Onay Tarihi')
    publication_date = fields.Datetime(string='Yayın Tarihi')
    expiry_date = fields.Date(string='Son Kullanım Tarihi')
    
    # İlişkiler
    partner_id = fields.Many2one(
        'res.partner',
        string='İlaç Firması',
        required=True
    )
    
    responsible_user_id = fields.Many2one(
        'res.users',
        string='Sorumlu Kullanıcı',
        default=lambda self: self.env.user
    )
    
    # İstatistikler
    view_count = fields.Integer(
        string='Görüntülenme Sayısı',
        readonly=True,
        default=0
    )
    
    download_count = fields.Integer(
        string='İndirme Sayısı',
        readonly=True,
        default=0
    )
    
    last_accessed = fields.Datetime(
        string='Son Erişim',
        readonly=True
    )
    
    # Analitik veriler için
    usage_analytics_ids = fields.One2many(
        'prospectus.usage.analytics',
        'prospectus_id',
        string='Kullanım Analitiği'
    )
    
    @api.model
    def create(self, vals):
        # Benzersiz kod oluştur
        vals['unique_code'] = str(uuid.uuid4())
        return super().create(vals)
    
    @api.depends('unique_code')
    def _compute_qr_code(self):
        for record in self:
            if record.unique_code:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.public_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_data = buffer.getvalue()
                
                record.qr_code_image = base64.b64encode(img_data)
    
    @api.depends('unique_code')
    def _compute_public_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.unique_code:
                record.public_url = f"{base_url}/digital_prospectus/{record.unique_code}"
    
    def action_submit_for_review(self):
        self.state = 'review'
        self.message_post(body=_('Prospektüs inceleme için gönderildi.'))
    
    def action_approve(self):
        self.state = 'approved'
        self.approval_date = fields.Datetime.now()
        self.message_post(body=_('Prospektüs onaylandı.'))
    
    def action_publish(self):
        self.state = 'published'
        self.publication_date = fields.Datetime.now()
        self.message_post(body=_('Prospektüs yayında.'))
    
    def action_cancel(self):
        self.state = 'cancelled'
        self.message_post(body=_('Prospektüs iptal edildi.'))
    
    def increment_view_count(self, user_info=None):
        """Görüntülenme sayısını artır ve analitik kayıt oluştur"""
        self.view_count += 1
        self.last_accessed = fields.Datetime.now()
        
        # Analitik kayıt oluştur
        self.env['prospectus.usage.analytics'].create({
            'prospectus_id': self.id,
            'action': 'view',
            'user_ip': user_info.get('ip') if user_info else None,
            'user_agent': user_info.get('user_agent') if user_info else None,
            'access_date': fields.Datetime.now()
        })
        
    def action_view_analytics(self):
        """Analitik görüntüleme aksiyonu"""
        self.ensure_one()
        return {
            'name': _('Kullanım Analitiği'),
            'type': 'ir.actions.act_window',
            'res_model': 'prospectus.usage.analytics',
            'view_mode': 'tree,graph,pivot',
            'domain': [('prospectus_id', '=', self.id)],
            'context': {'default_prospectus_id': self.id}
        }