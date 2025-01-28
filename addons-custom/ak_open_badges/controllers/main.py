from odoo import http, _, fields
from odoo.http import request
import json
from cryptography.exceptions import InvalidSignature
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


class OpenBadgesController(http.Controller):
    
    def _verify_signature(self, assertion_data, signature, public_key_pem):
        """Rozet imzasını doğrula"""
        try:
            # Public key'i yükle
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # JSON verisini string'e çevir (signature hariç)
            assertion_copy = assertion_data.copy()
            assertion_copy.pop('signature', None)
            assertion_string = json.dumps(assertion_copy, sort_keys=True)

            # İmzayı doğrula
            public_key.verify(
                base64.b64decode(signature),
                assertion_string.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, Exception):
            return False    
    
    @http.route(['/badge/verify/<string:token>'], type='http', auth='public', website=True)
    def verify_badge(self, token, download=None):
        """Badge doğrulama sayfası"""
        badges = request.env['badge.assertion'].sudo()
        badge = badges.search([('verification_token', '=', token)], limit=1)
        
        if not badge:
            return request.render('ak_open_badges.verification_error', {
                'error': 'Invalid verification token'
            })

        # PDF indir parametresi varsa ve sertifika mevcutsa
        if download and badge.certificate_file:
            return http.request.make_response(
                base64.b64decode(badge.certificate_file),
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', f'inline; filename=certificate_{token}.pdf')
                ]
            )

        verification_data = badge.get_verification_data()
        verification_status = {
            'is_valid': True,
            'messages': []
        }

        # İmza kontrolü
        if badge.verification_type == 'SignedBadge':
            assertion_data = badge.get_json_ld()
            signature = assertion_data.get('signature')
            public_key = badge.badge_class_id.issuer_id.public_key

            if not signature or not public_key:
                verification_status['is_valid'] = False
                verification_status['messages'].append('Missing signature or public key')
            elif not self._verify_signature(assertion_data, signature, public_key):
                verification_status['is_valid'] = False
                verification_status['messages'].append('Invalid signature')

        # Süre kontrolü
        if badge.expiration_date and badge.expiration_date < fields.Datetime.now():
            verification_status['is_valid'] = False
            verification_status['messages'].append('Badge has expired')

        # İptal kontrolü
        if badge.state == 'revoked':
            verification_status['is_valid'] = False
            verification_status['messages'].append('Badge has been revoked')

        return request.render('ak_open_badges.verification_page', {
            'badge': badge,
            'data': verification_data,
            'verification': verification_status
        })
    
    @http.route(['/badge/assertion/<int:assertion_id>'], type='http', auth='public', website=True)
    def get_assertion(self, assertion_id):
        """Open Badges Assertion JSON-LD endpoint"""
        assertion = request.env['badge.assertion'].sudo().browse(assertion_id)
        if not assertion.exists():
            return request.not_found()
            
        return request.make_response(
            json.dumps(assertion.get_json_ld()),
            headers=[('Content-Type', 'application/ld+json')]
        )
    
    @http.route(['/badge/class/<int:class_id>'], type='http', auth='public', website=True)
    def get_badge_class(self, class_id):
        """Open Badges BadgeClass JSON-LD endpoint"""
        badge_class = request.env['badge.class'].sudo().browse(class_id)
        if not badge_class.exists():
            return request.not_found()
            
        return request.make_response(
            json.dumps(badge_class.get_json_ld()),
            headers=[('Content-Type', 'application/ld+json')]
        )
        
        

        