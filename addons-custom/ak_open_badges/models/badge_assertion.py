import json
import uuid
import hashlib
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64


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
        # Mevcut verification_page template'ini kullanarak PDF oluştur
        pdf = self.env.ref('ak_open_badges.badge_certificate_report')._render_qweb_pdf(self.id)[0]
        
        filename = f'certificate_{self.verification_token}.pdf'
        self.write({
            'certificate_file': base64.b64encode(pdf),
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
    
    