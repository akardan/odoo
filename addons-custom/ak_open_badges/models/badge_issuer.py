from odoo import models, fields, api, _
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class BadgeIssuer(models.Model):
    _name = 'badge.issuer'
    _description = _('Badge Issuer Profile')
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Çevrilecek alanlar
    name = fields.Char(string=_('Name'), required=True, translate=True, tracking=True)
    description = fields.Text(string=_('Description'), translate=True, tracking=True)

    # Çevrilmeyecek alanlar
    url = fields.Char(string=_('URL'), required=True)
    email = fields.Char(string=_('Email'), required=True)
    image = fields.Binary(string=_("Issuer Logo"))
    image2 = fields.Binary(string=_("Second Issuer Logo"))
    public_key = fields.Text(string=_('Public Key for Verification'), readonly=True, tracking=True)
    private_key = fields.Text(string=_('Private Key'), readonly=True, groups="base.group_system")
    signature = fields.Binary(string='Issuer Signature', attachment=True)
    signature2 = fields.Binary(string='Second Issuer Signature', attachment=True)
    issuer_title = fields.Char(string=_('Issuer Title'))
    issuer_title2 = fields.Char(string=_('Second Issuer Title'))
    
    def get_json_ld(self):
        # Varsayılan dili kullan
        default_lang = 'en_US'
        self = self.with_context(lang=default_lang)
        
        return {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "Issuer",
            "id": self.url,
            "name": self.name,
            "url": self.url,
            "email": self.email,
            "description": self.description or "",
        }
        
    def generate_key_pair(self):
        # RSA key pair oluştur
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        # Public key'i PEM formatında kaydet
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Private key'i PEM formatında kaydet
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        self.write({
            'public_key': pem_public.decode('utf-8'),
            'private_key': pem_private.decode('utf-8')
        })        
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Key pair generated successfully'),
                'type': 'success',
                'sticky': False,
            }
        }
