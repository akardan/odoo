from odoo import models, fields, api, _
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class BadgeIssuer(models.Model):
    _name = 'badge.issuer'
    _description = _('Badge Issuer Profile')
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string=_('Name'), required=True)
    url = fields.Char(string=_('URL'), required=True)
    email = fields.Char(string=_('Email'), required=True)
    description = fields.Text(string=_('Description'))
    image = fields.Binary(string=_("Issuer Logo"))
    public_key = fields.Text(string=_('Public Key for Verification'), readonly=True, tracking=True)
    private_key = fields.Text(string=_('Private Key'), readonly=True, groups="base.group_system")
    signature = fields.Binary(string='Signature', attachment=True)
    
    def get_json_ld(self):
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
