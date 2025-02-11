import json
import uuid
import hashlib
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
import logging

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import tempfile

_logger = logging.getLogger(__name__)

class BadgeAssertion(models.Model):
    _name = 'badge.assertion'
    _description = _('Open Badge Assertion')
    _inherit = ['mail.thread', 'mail.activity.mixin', 'base']

    name = fields.Char(compute='_compute_name', store=True)
    badge_class_id = fields.Many2one('badge.class', string=_('Certificate Class'), required=True, tracking=True)
    recipient_id = fields.Many2one('res.partner', string=_('Recipient'), required=True)
    recipient_type = fields.Selection([
        ('email', _('Email')),
        ('url', _('URL')),
        ('telephone', _('Telephone')),
    ], string=_('Recipient Type'), default='email', required=True, tracking=True)
    recipient_identity = fields.Char(string=_('Recipient Identity'), compute='_compute_recipient_identity', store=True)
    recipient_hashed = fields.Boolean(string=_('Hash Recipient'), default=True)
    recipient_salt = fields.Char(
        string=_('Salt'), 
        compute='_compute_recipient_salt', 
        store=True
    )
    
    issuance_date = fields.Datetime(string=_('Issue Date'), default=fields.Datetime.now, required=True, tracking=True)
    expiration_date = fields.Datetime(string=_('Expiry Date'), tracking=True)
    
    evidence = fields.One2many('badge.evidence', 'assertion_id', string=_('Evidence'))
    verification_type = fields.Selection([
        ('HostedBadge', _('Hosted')),
        ('SignedBadge', _('Signed')),
    ], string=_('Verification Type'), default='HostedBadge', required=True)

    verification_token = fields.Char(string=_('Certificate ID'), compute='_compute_verification_token', store=True)
    
    qr_code = fields.Binary(string=_('QR Code'), compute='_compute_qr_code', store=True)
    assertion_url = fields.Char(string=_('Verification URL'), compute='_compute_assertion_url')

    state = fields.Selection([
        ('draft', _('Draft')),
        ('issued', _('Issued')),
        ('revoked', _('Revoked'))
    ], string=_('Status'), default='draft', tracking=True)

    certificate_file = fields.Binary(string=_('Certificate File'), attachment=True)
    certificate_filename = fields.Char(string=_('Certificate Filename'))
    signature = fields.Text(
        string='Digital Signature', 
        readonly=True, 
        copy=False,
        help=_('Digital signature for SignedBadge verification type')
    )


    # Çeviri metinlerini hazırla
    translations = {
        'certifies_that': _('This certifies that'),
        'completed': _('has successfully completed the'),
        'signature': _('Signature'),
        'issue_date': _('Issue Date'),
        'expiry_date': _('Expiry Date'),
        'certificate_id': _('Certificate ID'),
    }

    def _translate(self, source, lang_code=None):
        """Helper method to get translation"""
        if not lang_code:
            lang_code = self.env.user.lang
            
        # Use Odoo's built-in translation method
        return self.env['ir.translation']._get_source(
            name=None,         # No specific model name
            types=['code'],    # Translation type
            lang=lang_code,    # Target language
            source=source      # Source string to translate
        ) or ''
    
    def get_field_caption(self, field_name, lang):
        return self.env['ir.model.fields'].with_context(lang=lang).search([
            ('model', '=', self._name),
            ('name', '=', field_name)
        ]).field_description
        
    def get_related_field_caption(self, model, field_path, lang):
        if not field_path:
            return None

        field_name, _, remaining_path = field_path.partition('.')
        # model = self.env[self._name]
        field = model._fields.get(field_name)

        if not field:
            return None

        caption = self.env['ir.model.fields'].with_context(lang=lang).search([
            ('model', '=', model._name),
            ('name', '=', field_name)
        ]).field_description

        if not remaining_path:
            return caption

        if field.type == 'many2one':
            return self.get_related_field_caption(
                self.env[field.comodel_name], 
                remaining_path, 
                lang
            )
        else:
            return caption        
            
    def _generate_certificate_pdf(self):
        self.ensure_one()
        
        # Dilleri al
        primary_lang = self.env['res.lang'].search([('code', '=', self.badge_class_id.primary_lang)], limit=1)
        secondary_lang = self.env['res.lang'].search([('code', '=', self.badge_class_id.secondary_lang)], limit=1)

        # Birincil ve ikincil dilde içerikleri al
        primary_content = self.with_context(lang=primary_lang.code)
        secondary_content = self.with_context(lang=secondary_lang.code) if secondary_lang else None


        # Font yolunu ayarla
        module_path = os.path.dirname(os.path.dirname(__file__))
        pirata_font_path = os.path.join(module_path, 'static/fonts', 'PirataOne-Regular.ttf')
        ephesis_font_path = os.path.join(module_path, 'static/fonts', 'Ephesis-Regular.ttf')
        PTSansNarrow_Regular_path = os.path.join(module_path, 'static/fonts', 'PTSansNarrow-Regular.ttf')
        PTSansNarrow_Bold_path = os.path.join(module_path, 'static/fonts', 'PTSansNarrow-Bold.ttf')

        # Fontu kaydet
        pdfmetrics.registerFont(TTFont('PirataOne', pirata_font_path))
        pdfmetrics.registerFont(TTFont('Ephesis', ephesis_font_path))
        pdfmetrics.registerFont(TTFont('PTSansNarrow', PTSansNarrow_Regular_path))
        pdfmetrics.registerFont(TTFont('PTSansNarrow-Bold', PTSansNarrow_Bold_path))

        # A4 Landscape
        width, height = landscape(A4)
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, 
            pagesize=landscape(A4),
            leftMargin=1.5*cm,
            rightMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        story = []
        styles = getSampleStyleSheet()


        # Özel stiller
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName='PirataOne',
            fontSize=42,
            leading=35,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1B1B1B'),
            spaceAfter=5
        )
        # İkincil dil için başlık stili
        title_style_secondary = ParagraphStyle(
            'CustomTitleSecondary',
            parent=title_style,
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'),
            spaceAfter=0
        )

        subtitle_style = ParagraphStyle(
            'CustomSubTitle',
            parent=styles['Normal'],
            fontName='PTSansNarrow',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#333333'),
            spaceAfter=0
        )

        subtitle_style_secondary = ParagraphStyle(
            'CustomSubTitleSecondary',
            parent=subtitle_style,
            fontSize=12,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'),
            spaceAfter=0
        )


        name_style = ParagraphStyle(
            'NameStyle',
            parent=styles['Normal'],
            fontName='Ephesis',
            fontSize=36,
            leading=40,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1B1B1B'),
            spaceAfter=5
        )

        course_style = ParagraphStyle(
            'CourseStyle',
            parent=styles['Normal'],
            fontName='Ephesis',
            fontSize=32,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1B1B1B'),
            spaceAfter=5
        )

        course_style_secondary = ParagraphStyle(
            'CourseStyleSecondary',
            parent=styles['Normal'],
            fontName='Ephesis',
            fontSize=24,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'),
            spaceAfter=15
        )

        # İçerik
        story.append(Spacer(1, 1*cm))
        
        # Başlık
        title = Paragraph(f"<b>{primary_content.badge_class_id.badge_type_id.name}</b>", title_style)
        if secondary_content:
            title_secondary = Paragraph(f"<b>{secondary_content.badge_class_id.badge_type_id.name}</b>", title_style_secondary)
        else:
            title_secondary = Paragraph('&nbsp;', title_style_secondary)
        story.append(title)
        story.append(title_secondary)
        
        story.append(Spacer(1, 0.5*cm))
        
        # phrase4recipient
        subtitle = Paragraph(primary_content.badge_class_id.badge_type_id.phrase4recipient, subtitle_style)
        if secondary_content:
            subtitle_sec = Paragraph(secondary_content.badge_class_id.badge_type_id.phrase4recipient, subtitle_style_secondary)
        else:
            subtitle_sec = Paragraph('&nbsp;', subtitle_style_secondary)
        story.append(subtitle)
        story.append(subtitle_sec)
                
        # İsim
        name = Paragraph(f"<b>{self.recipient_id.name}</b>", name_style)
        story.append(name)
        
        # phrase4certificate
        course_info = Paragraph(primary_content.badge_class_id.badge_type_id.phrase4certificate, subtitle_style)
        if secondary_content:
            course_info_sec = Paragraph(secondary_content.badge_class_id.badge_type_id.phrase4certificate, subtitle_style_secondary)
        else:
            course_info_sec = Paragraph('&nbsp;', subtitle_style_secondary)
        story.append(course_info)
        story.append(course_info_sec)
        
        # Kurs adı
        course_name = Paragraph(f"<b>{primary_content.badge_class_id.name}</b>", course_style)
        if secondary_content:
            course_name_secondary = Paragraph(f"<b>{secondary_content.badge_class_id.name}</b>", course_style_secondary)
        else:
            course_name_secondary = Paragraph('&nbsp;', course_style_secondary)
        story.append(course_name)
        story.append(course_name_secondary)

        # phrase_last
        after_course_info = Paragraph(primary_content.badge_class_id.badge_type_id.phrase_last, subtitle_style)
        if secondary_content:
            after_course_info_sec = Paragraph(secondary_content.badge_class_id.badge_type_id.phrase_last, subtitle_style_secondary)
        else:
            after_course_info_sec = Paragraph('&nbsp;', subtitle_style_secondary)
        story.append(after_course_info)
        story.append(after_course_info_sec)

        # story.append(Spacer(1, 2*cm))

        # Altın renkli çerçeve
        def draw_certificate_template(canvas, doc):
            # Sayfanın gerçek boyutlarını al
            page_width = doc.pagesize[0]  # Landscape A4 genişlik
            page_height = doc.pagesize[1] # Landscape A4 yükseklik

            canvas.saveState()
            
            # Background image ekle
            try:
                # Background image yolu
                bg_path = os.path.join(module_path, 'static', 'src', 'img', 'background-pattern 05.png')
                
                # Background'u tüm sayfaya yayarak yerleştir
                canvas.drawImage(
                    bg_path, 
                    0,  # x pozisyonu - en soldan başla
                    0,  # y pozisyonu - en alttan başla
                    width=page_width,  # sayfanın tam genişliği
                    height=page_height,  # sayfanın tam yüksekliği
                    mask='auto',
                    preserveAspectRatio=False  # Görüntüyü sayfaya sığdır
                )
            except Exception as e:
                _logger.error(f"Background image yüklenemedi: {str(e)}")

            # canvas.setFillColorRGB(1, 1, 1, 0.9)  # Beyaz arka plan %90 opaklık
            # canvas.rect(0, 0, page_width, page_height, fill=True)

            # Dış çerçeve
            canvas.setStrokeColor(colors.HexColor('#D4AF37'))
            canvas.setLineWidth(2)
            
            # Kenar boşlukları - 1cm azaltıldı (2cm'den 1cm'ye)
            margin = 1*cm
            
            # Dış çerçeve - sayfa kenarlarından margin kadar içeride
            canvas.rect(
                margin,                  
                margin,                  
                page_width - 2*margin,   
                page_height - 2*margin   
            )
            
            # İç çerçeve - 1cm azaltıldı (3cm'den 2cm'ye)
            inner_margin = 2*cm
            canvas.setLineWidth(1)
            canvas.rect(
                inner_margin,
                inner_margin,
                page_width - 2*inner_margin,
                page_height - 2*inner_margin
            )
            
            # Alt süsleme - dış çerçeve ile aynı genişlikte
            canvas.setLineWidth(1)
            p = canvas.beginPath()
            p.moveTo(margin, margin + 1*cm)
            p.curveTo(
                page_width/2, margin + 0.5*cm,     
                page_width/2, margin + 0.5*cm,     
                page_width - margin, margin + 1*cm  
            )
            canvas.drawPath(p)
            
            # Üst süsleme - dış çerçeve ile aynı genişlikte
            p = canvas.beginPath()
            p.moveTo(margin, page_height - margin - 1*cm)
            p.curveTo(
                page_width/2, page_height - margin - 0.5*cm,
                page_width/2, page_height - margin - 0.5*cm,
                page_width - margin, page_height - margin - 1*cm
            )
            canvas.drawPath(p)

            # Logo ekle (sağ üst)
            if self.badge_class_id.issuer_id.image:
                logo_data = BytesIO(base64.b64decode(self.badge_class_id.issuer_id.image))
                logo = ImageReader(logo_data)
                # Logo boyutları (3cm x 3cm)
                logo_width = 5*cm
                logo_height = 2*cm
                # Pozisyon: sağ üst köşeden 2cm içeride
                x = page_width - logo_width - 2.3*cm
                y = page_height - logo_height - 2.2*cm
                
                canvas.drawImage(
                    logo, x, y, 
                    width=logo_width, 
                    height=logo_height, 
                    preserveAspectRatio=True, 
                    mask='auto'
                )
            # Logo ekle (sol üst)
            if self.badge_class_id.issuer_id.image2: 
                logo_data = BytesIO(base64.b64decode(self.badge_class_id.issuer_id.image2))
                logo = ImageReader(logo_data)
                # Logo boyutları (3cm x 3cm)
                logo_width = 3.5*cm
                logo_height = 2*cm
                # Pozisyon: sağ üst köşeden 2cm içeride
                x = 2.3*cm
                y = page_height - logo_height - 2.2*cm
                
                canvas.drawImage(
                    logo, x, y, 
                    width=logo_width, 
                    height=logo_height, 
                    preserveAspectRatio=True, 
                    mask='auto'
                )
            # QR Code ve Detay bilgileri için ortak y pozisyonu
            detail_y = 4*cm  # QR Code ile aynı hizadan başla

            # Badge Logo (sol alt)
            if self.badge_class_id.image:
                badge_logo_data = BytesIO(base64.b64decode(self.badge_class_id.image))
                badge_logo = ImageReader(badge_logo_data)
                
                # Badge logo boyutları
                badge_width = 3*cm
                badge_height = 3*cm
                
                # Pozisyon: sol alt köşeden 2cm içeride
                x = 2.5*cm
                y = detail_y -1*cm
                
                # Badge logo'yu yerleştir
                canvas.drawImage(
                    badge_logo, x, y, 
                    width=badge_width, 
                    height=badge_height, 
                    preserveAspectRatio=True, 
                    mask='auto'  # Transparanlık için
                )                    

            # İmza bölümü (orta alt)
            sig_x = page_width/3 - 2.5*cm  # İmzayı ortalamak için
            sig_y = detail_y
            
            # İmza başlığı çift dilli
            sig_text_primary = primary_content.get_related_field_caption(self, 'badge_class_id.issuer_id.signature', primary_lang.code)
            if secondary_content:
                sig_text_secondary = secondary_content.get_related_field_caption(self, 'badge_class_id.issuer_id.signature', secondary_lang.code)
            else:
                sig_text_secondary = '&nbsp;'
            
            if self.badge_class_id.issuer_id.signature2:
                canvas.setFont('PTSansNarrow-Bold', 12)
                canvas.drawString(sig_x + 3.0*cm, sig_y + 1.5*cm, sig_text_primary)
                canvas.setFont('PTSansNarrow', 10)
                canvas.drawString(sig_x + 3.3*cm, sig_y + 1.1*cm, sig_text_secondary)
            else:
                canvas.setFont('PTSansNarrow-Bold', 12)
                canvas.drawString(sig_x + 3.0*cm, sig_y + 1.5*cm, sig_text_primary)
                canvas.setFont('PTSansNarrow', 10)
                canvas.drawString(sig_x + 3.3*cm, sig_y + 1.1*cm, sig_text_secondary)

            canvas.setFont('PTSansNarrow', 10)
            
            # İmza çizgisi
            if self.badge_class_id.issuer_id.signature2:
                canvas.line(sig_x - 0*cm, sig_y + 0.9*cm, sig_x + 9*cm, sig_y + 0.9*cm)
                # for i in range(11):
                #     canvas.circle(sig_x - 0*cm + i*cm, sig_y + 0.9*cm, 1, stroke=1, fill=1)
            else:
                canvas.line(sig_x + 2*cm, sig_y + 0.9*cm, sig_x + 7*cm, sig_y + 0.9*cm)

            # Issuer2 Title ekle
            if self.badge_class_id.issuer_id.issuer_title2:
                canvas.setFont('PTSansNarrow-Bold', 10)
                issuer_title2_lines = self.badge_class_id.issuer_id.issuer_title2.split('\n')
                for i, line in enumerate(issuer_title2_lines):
                    canvas.drawString(sig_x + 0.5*cm, sig_y + 0.3*cm - i*0.4*cm, line)
                
            # Issuer Title ekle
            if self.badge_class_id.issuer_id.issuer_title:
                canvas.setFont('PTSansNarrow-Bold', 10)
                issuer_title_lines = self.badge_class_id.issuer_id.issuer_title.split('\n')
                for i, line in enumerate(issuer_title_lines):
                    if self.badge_class_id.issuer_id.signature2:
                        canvas.drawString(sig_x + 5*cm, sig_y + 0.3*cm - i*0.4*cm, line)
                    else:
                        canvas.drawString(sig_x + 3*cm, sig_y + 0.3*cm - i*0.4*cm, line)

            # Issuer2 signature ekle
            if self.badge_class_id.issuer_id.signature2:
                signature_data = BytesIO(base64.b64decode(self.badge_class_id.issuer_id.signature2))
                signature = ImageReader(signature_data)
                
                # İmza pozisyonu - footer table'ın üçüncü sütununun üzerine gelecek şekilde
                sig_width = 3*cm
                sig_height = 2.5*cm
                
                canvas.drawImage(
                    signature, sig_x + 0.3*cm, sig_y - 2.0*cm , 
                    width=sig_width, 
                    height=sig_height, 
                    preserveAspectRatio=True, 
                    mask='auto'
                )
            
            # Issuer signature ekle
            if self.badge_class_id.issuer_id.signature:
                signature_data = BytesIO(base64.b64decode(self.badge_class_id.issuer_id.signature))
                signature = ImageReader(signature_data)
                
                # İmza pozisyonu - footer table'ın üçüncü sütununun üzerine gelecek şekilde
                sig_width = 3*cm
                sig_height = 2.5*cm
                if self.badge_class_id.issuer_id.signature2:
                    canvas.drawImage(
                        signature, sig_x + 5.0*cm, sig_y - 2.0*cm , 
                        width=sig_width, 
                        height=sig_height, 
                        preserveAspectRatio=True, 
                        mask='auto'
                    )
                else:
                    canvas.drawImage(
                        signature, sig_x + 3.0*cm, sig_y - 2.0*cm , 
                        width=sig_width, 
                        height=sig_height, 
                        preserveAspectRatio=True, 
                        mask='auto'
                    )

            #Qr Code ekle
            if self.qr_code:
                qr_code_data = BytesIO(base64.b64decode(self.qr_code))
                qr_code = ImageReader(qr_code_data)
                
                # QR Code boyutları
                qr_width = 2*cm
                qr_height = 2*cm
                
                # QR Code pozisyonu: sağ alt köşeden 2cm içeride
                qr_x = page_width - qr_width - 2.5*cm
                qr_y = detail_y

                # QR Code'yu yerleştir
                canvas.drawImage(
                    qr_code, qr_x, qr_y - 1.8*cm,
                    width=qr_width,
                    height=qr_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )

                # Detay bilgilerini QR Code'un soluna yerleştir
                details_x = qr_x - 7*cm  # QR Code'dan 6cm sol

                # Çift dilli detay metinleri
                details = [
                    (
                        f"{primary_content.get_field_caption('issuance_date', primary_lang.code)}" +
                        (f" / {secondary_content.get_field_caption('issuance_date', secondary_lang.code)}" if secondary_content else '&nbsp;') +
                        f": {self.issuance_date.strftime('%d/%m/%Y')}", 
                        0.5
                    ),
                    (
                        f"{primary_content.get_field_caption('expiration_date', primary_lang.code)}" +
                        (f" / {secondary_content.get_field_caption('expiration_date', secondary_lang.code)}" if secondary_content else '&nbsp;') +
                        f": {self.expiration_date.strftime('%d/%m/%Y') if self.expiration_date else 'N/A'}", 
                        1.0
                    ),
                    (
                        f"{primary_content.get_field_caption('verification_token', primary_lang.code)}" +
                        (f" / {secondary_content.get_field_caption('verification_token', secondary_lang.code)}" if secondary_content else '&nbsp;') +
                        f": {self.verification_token}",
                        1.5
                    )
                ]
                
                canvas.setFont('PTSansNarrow-Bold', 10)
                for text, offset in details:
                    canvas.drawString(details_x, detail_y - offset*cm, text)
                
            canvas.restoreState()            
            
    
        # PDF oluştur
        doc.build(story, onFirstPage=draw_certificate_template, onLaterPages=draw_certificate_template)
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()

        # PDF'i kaydet
        filename = f'certificate_{self.verification_token}.pdf'
        self.write({
            'certificate_file': base64.b64encode(pdf_value),
            'certificate_filename': filename
        })

        return True

    @api.depends('create_date', 'recipient_id')
    def _compute_recipient_salt(self):
        for record in self:
            if record.create_date and record.recipient_id:
                # recipient_id ve create_date kullanarak benzersiz salt oluştur
                record.recipient_salt = hashlib.sha256(
                    f"{record.create_date}-{record.recipient_id.id}".encode()
                ).hexdigest()[:16]

    @api.depends('create_date', 'badge_class_id')
    def _compute_verification_token(self):
        for record in self:
            if record.create_date and record.badge_class_id:
                record.verification_token = hashlib.sha256(
                    f"{record.create_date}-{record.badge_class_id.id}-{record.id}".encode()
                ).hexdigest()[:16]
                
    @api.depends('badge_class_id', 'recipient_id')
    def _compute_name(self):
        for record in self:
            if record.badge_class_id and record.recipient_id:
                record.name = f"{record.badge_class_id.name} - {record.recipient_id.name}"

    @api.depends('assertion_url')  # assertion_url'e bağımlı hale getirildi
    def _compute_qr_code(self):
        import qrcode
        import base64
        from io import BytesIO
        
        for record in self:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L)
            qr.add_data(record.assertion_url)
            qr.make(fit=True)
            
            img = qr.make_image()
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            record.qr_code = base64.b64encode(buffer.getvalue())

    @api.depends('verification_token')
    def _compute_assertion_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.verification_token:
                record.assertion_url = f"{base_url}/badge/verify/{record.verification_token}"
            else:
                record.assertion_url = False
                        
    def get_verification_data(self):
        """Doğrulama için gerekli tüm verileri döndürür."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        return {
            'badge_name': self.badge_class_id.name,
            'recipient_name': self.recipient_id.name,
            'issuer_name': self.badge_class_id.issuer_id.name,
            'issue_date': self.issuance_date.isoformat(),
            'expiry_date': self.expiration_date and self.expiration_date.isoformat() or False,
            'verification_url': self.assertion_url,
            'verification_type': self.verification_type,
            'status': self.state,  # 'draft', 'issued', veya 'revoked' döner
            'badge_class_url': f"{base_url}/badge/class/{self.badge_class_id.id}",
            'assertion_json_url': f"{base_url}/badge/assertion/{self.id}"
        }

    def action_revoke(self):
        """Rozeti iptal et"""
        self.ensure_one()
        if self.state != 'issued':
            raise UserError(_('Only issued badges can be revoked.'))
        
        self.write({
            'state': 'revoked',
        })
        return True
    
    def get_json_ld(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        assertion = {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "Assertion",
            "id": f"{base_url}/badge/assertion/{self.id}",
            "badge": self.badge_class_id.get_json_ld(),
            "recipient": {
                "type": self.recipient_type,
                "identity": self.recipient_identity,
                "hashed": self.recipient_hashed,
                "salt": self.recipient_salt if self.recipient_hashed else None,
            },
            "issuedOn": self.issuance_date.isoformat(),     # Tarih formatı: 2021-01-01T00:00:00
            "verification": {
                "type": self.verification_type,
                "url": self.assertion_url
            }
        }

        if self.expiration_date:
            assertion["expires"] = self.expiration_date.isoformat()

        if self.evidence:
            assertion["evidence"] = [ev.get_json_ld() for ev in self.evidence]

        if self.state == 'revoked':
            assertion["revoked"] = True
            # assertion["revocationReason"] = self.revocation_reason

        # SignedBadge için imza ekle
        if self.verification_type == 'SignedBadge' and hasattr(self, 'signature') and self.signature:
            assertion['signature'] = self.signature

        return assertion

    def _get_salt(self):
            """Benzersiz bir salt değeri oluştur"""
            return str(uuid.uuid4())
        
    def _sign_assertion(self):
        """Rozeti private key ile imzala"""
        self.ensure_one()

        if self.verification_type != 'SignedBadge':
            return False

        private_key_pem = self.badge_class_id.issuer_id.private_key
        if not private_key_pem:
            raise UserError(_('No private key found for issuer. Please generate keys first.'))

        # JSON-LD'yi string'e çevir (signature alanı hariç)
        assertion_data = self.get_json_ld()
        assertion_data.pop('signature', None)
        assertion_string = json.dumps(assertion_data, sort_keys=True)
        
        try:
            # Private key'i yükle
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )

            # İmzala
            signature = private_key.sign(
                assertion_string.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            raise UserError(_('Error signing badge: %s') % str(e))

    def action_issue(self):
        """Issue the badge with signature if needed"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft badges can be issued'))

        # Önce state ve issuance_date'i güncelle
        self.write({
            'state': 'issued',
            'issuance_date': self.issuance_date or fields.Datetime.now()
        })

        # Alignment'lardan evidence oluştur
        if self.badge_class_id.alignment:
            # Önce mevcut evidence'ları sil
            self.evidence.unlink()
            
            for alignment in self.badge_class_id.alignment:
                # Primary ve secondary dilleri al
                primary_lang = self.badge_class_id.primary_lang
                secondary_lang = self.badge_class_id.secondary_lang

                # İki dildeki değerleri al
                target_name_primary = alignment.with_context(lang=primary_lang).target_name
                target_name_secondary = alignment.with_context(lang=secondary_lang).target_name or ''
                
                target_desc_primary = alignment.with_context(lang=primary_lang).target_description
                target_desc_secondary = alignment.with_context(lang=secondary_lang).target_description  or ''
                
                target_framework_primary = alignment.with_context(lang=primary_lang).target_framework
                target_framework_secondary = alignment.with_context(lang=secondary_lang).target_framework or ''

                # Evidence kaydını primary dil değerleriyle oluştur
                evidence = self.env['badge.evidence'].with_context(lang=primary_lang).create({
                    'assertion_id': self.id,
                    'name': target_name_primary,
                    'description': target_desc_primary,
                    'narrative': f"Demonstrated competency in {target_name_primary} according to {target_framework_primary}",
                    'genre': 'Hedef Bazlı Yetkinlik' if primary_lang == 'tr_TR' else 'Alignment Based Competency',
                    'id': alignment.target_url
                })

                # Secondary dil için değerleri güncelle
                if secondary_lang:
                    evidence.with_context(lang=secondary_lang).write({
                        'name': target_name_secondary,
                        'description': target_desc_secondary,
                        'narrative': f"Demonstrated competency in {target_name_secondary} according to {target_framework_secondary}",
                        'genre': 'Hedef Bazlı Yetkinlik' if secondary_lang == 'tr_TR' else 'Alignment Based Competency',
                    })


        if self.verification_type == 'SignedBadge':
            signature = self._sign_assertion()
            if not signature:
                raise UserError(_('Failed to sign the badge'))
            
            # İmzayı kaydet
            self.write({
                'signature': signature  # İmzayı kaydet
            })
       
        # Sertifikayı oluştur
        self._generate_certificate_pdf()

        return True

