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
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='_compute_name', store=True)
    badge_class_id = fields.Many2one('badge.class', string=_('Badge Class'), required=True, tracking=True)
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
    expiration_date = fields.Datetime(string=_('Expiry Date'))
    
    evidence = fields.One2many('badge.evidence', 'assertion_id', string=_('Evidence'))
    verification_type = fields.Selection([
        ('HostedBadge', _('Hosted')),
        ('SignedBadge', _('Signed')),
    ], string=_('Verification Type'), default='HostedBadge', required=True)

    verification_token = fields.Char(string=_('Verification Token'), compute='_compute_verification_token', store=True)
    
    qr_code = fields.Binary(string=_('QR Code'), compute='_compute_qr_code', store=True)
    assertion_url = fields.Char(string=_('Verification URL'), compute='_compute_assertion_url')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('revoked', 'Revoked')
    ], string='Status', default='draft', tracking=True)

    certificate_file = fields.Binary(string=_('Certificate File'), attachment=True)
    certificate_filename = fields.Char(string=_('Certificate Filename'))

    def _generate_certificate_pdf(self):
        self.ensure_one()
        
        # Font yolunu ayarla
        module_path = os.path.dirname(os.path.dirname(__file__))
        pirata_font_path = os.path.join(module_path, 'static/fonts', 'PirataOne-Regular.ttf')
        ephesis_font_path = os.path.join(module_path, 'static/fonts', 'Ephesis-Regular.ttf')

        # Fontu kaydet
        pdfmetrics.registerFont(TTFont('PirataOne', pirata_font_path))
        pdfmetrics.registerFont(TTFont('Ephesis', ephesis_font_path))

        
        
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
            leading=44,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1B1B1B'),
            spaceAfter=30
        )

        subtitle_style = ParagraphStyle(
            'CustomSubTitle',
            parent=styles['Normal'],
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        )

        name_style = ParagraphStyle(
            'NameStyle',
            parent=styles['Normal'],
            fontName='Ephesis',
            fontSize=36,
            leading=34,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1B1B1B'),
            spaceAfter=20
        )

        course_style = ParagraphStyle(
            'CourseStyle',
            parent=styles['Normal'],
            fontName='Ephesis',
            fontSize=32,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1B1B1B'),
            spaceAfter=15
        )

        # İçerik
        story.append(Spacer(1, 1*cm))
        
        # Başlık
        title = Paragraph(f"<b>{self.badge_class_id.badge_type_id.name}</b>", title_style)
        story.append(title)
        
        story.append(Spacer(1, 0.5*cm))
        
        # Alt başlık
        subtitle = Paragraph("This certifies that", subtitle_style)
        story.append(subtitle)
        
        # İsim
        name = Paragraph(f"<b>{self.recipient_id.name}</b>", name_style)
        story.append(name)
        
        # Kurs bilgisi
        course_info = Paragraph("has successfully completed the", subtitle_style)
        story.append(course_info)
        
        # Kurs adı
        course_name = Paragraph(f"<b>{self.badge_class_id.name}</b>", course_style)
        story.append(course_name)
        
        story.append(Spacer(1, 2*cm))

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

            # Logo ekle
            if self.badge_class_id.issuer_id.image:
                logo_data = BytesIO(base64.b64decode(self.badge_class_id.issuer_id.image))
                logo = ImageReader(logo_data)
                # Logo boyutları (3cm x 3cm)
                logo_width = 5*cm
                logo_height = 3*cm
                # Pozisyon: sağ üst köşeden 2cm içeride
                x = page_width - logo_width - 2*cm
                y = page_height - logo_height - 2*cm
                
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
            sig_x = page_width/2 - 1.5*cm  # İmzayı ortalamak için
            sig_y = detail_y
            
            canvas.setFont('Helvetica-Bold', 10)
            canvas.drawString(sig_x - 0.5*cm, sig_y + 1.5*cm, "Issuer Signature")
            canvas.setFont('Helvetica', 10)
            
            # İmza çizgisi
            canvas.line(sig_x - 1.0*cm, sig_y + 1.0*cm, sig_x + 3*cm, sig_y + 1.0*cm)

            # İmza ekle
            if self.badge_class_id.issuer_id.signature:
                signature_data = BytesIO(base64.b64decode(self.badge_class_id.issuer_id.signature))
                signature = ImageReader(signature_data)
                
                # İmza pozisyonu - footer table'ın üçüncü sütununun üzerine gelecek şekilde
                sig_width = 3*cm
                sig_height = 2.5*cm
                
                canvas.drawImage(
                    signature, sig_x - 0.5*cm, sig_y - 1.5*cm , 
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
                details_x = qr_x - 6*cm  # QR Code'dan 6cm sol
                canvas.setFont('Helvetica-Bold', 10)
                
                # Bilgileri alt alta yaz
                canvas.drawString(details_x, detail_y - 0.5*cm, f"Issue Date   : {self.issuance_date.strftime('%d/%m/%Y')}")
                canvas.drawString(details_x, detail_y - 1.0*cm, f"Expiry Date : {self.expiration_date.strftime('%d/%m/%Y') if self.expiration_date else 'N/A'}")
                canvas.drawString(details_x, detail_y - 1.5*cm, f"Certificate ID: {self.verification_token}")
                
                
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

    # def _generate_certificate_pdf(self):
    #     self.ensure_one()
        
    #     # Debug için önce raporun detaylarını kontrol edelim
    #     report = self.env['ir.actions.report'].sudo().search([
    #         ('report_name', '=', 'ak_open_badges.badge_certificate_template')
    #     ], limit=1)
        
    #     if not report:
    #         raise ValueError("Rapor tanımı bulunamadı")
            
    #     try:
    #         # convert_to_pdf deneyelim
    #         pdf = report.sudo().with_context(
    #             active_model='badge.assertion',
    #             active_id=self.id
    #         ).convert_to_pdf([self.id])
            
    #         # report_render_qweb_pdf deneyelim ve farklı context kullanalım
    #         # pdf = report.sudo().with_context(
    #         #     active_model=self._name,
    #         #     active_id=self.id,
    #         # )._render_qweb_pdf(self.id)[0]
            
    #         filename = f'certificate_{self.verification_token}.pdf'
    #         self.write({
    #             'certificate_file': base64.b64encode(pdf),
    #             'certificate_filename': filename
    #         })
    #         return True
            
    #     except Exception as e:
    #         # Hata durumunda daha detaylı bilgi alalım
    #         _logger.error(f"PDF oluşturma hatası: {str(e)}")
    #         _logger.error(f"Report ID: {report.id}")
    #         _logger.error(f"Record ID: {self.id}")
    #         _logger.error(f"Model: {self._name}")
    #         raise

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
                    f"{record.create_date}-{record.badge_class_id.id}".encode()
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
            'issue_date': self.issuance_date.strftime('%Y-%m-%d %H:%M:%S'),
            'expiry_date': self.expiration_date and self.expiration_date.strftime('%Y-%m-%d %H:%M:%S') or False,
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
            "issuedOn": self.issuance_date.isoformat(),
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

        if self.verification_type == 'SignedBadge':
            signature = self._sign_assertion()
            if not signature:
                raise UserError(_('Failed to sign the badge'))
            
        self.write({
            'state': 'issued',
            'issuance_date': fields.Datetime.now()
        })
        
        
        # Sertifikayı oluştur
        self._generate_certificate_pdf()


        return True
    
    