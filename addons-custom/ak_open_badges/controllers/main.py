from odoo import http, _, fields
from odoo.http import request
import json
from cryptography.exceptions import InvalidSignature
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import logging

_logger = logging.getLogger(__name__)

class OpenBadgesController(http.Controller):
    
    def _verify_signature(self, assertion_data, signature, public_key_pem):
        """Rozet imzasını doğrula"""
        try:
            # Debug log ekleyelim
            _logger.info("=== Signature Verification Debug ===")
            _logger.info(f"Assertion Data Type: {type(assertion_data)}")
            _logger.info(f"Signature Type: {type(signature)}")

            # Public key'i yükle
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # JSON verisini string'e çevir (signature hariç)
            assertion_copy = assertion_data.copy()
            assertion_copy.pop('signature', None)
            assertion_string = json.dumps(assertion_copy, sort_keys=True)

            _logger.info(f"Data to verify: {assertion_string}")

            # İmzayı doğrula
            try:
                public_key.verify(
                    base64.b64decode(signature),
                    assertion_string.encode(),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                _logger.info("Signature verification successful!")
                return True
            except InvalidSignature:
                _logger.error("Invalid signature detected!")
                return False
        except Exception as e:
            _logger.error(f"Verification error: {str(e)}")
            return False   
    
    @http.route(['/badge/verify/<string:token>'], type='http', auth='public', website=True)
    def verify_badge(self, token):
        """Badge doğrulama sayfası"""
        badges = request.env['badge.assertion'].sudo()
        badge = badges.search([('verification_token', '=', token)], limit=1)

        # Debug logları
        _logger.info("=== Badge Verification Debug ===")
        _logger.info(f"Token: {token}")
        _logger.info(f"Badge Found: {bool(badge)}")
        _logger.info(f"Verification Type: {badge.verification_type}")
        _logger.info(f"Badge Class Issuer: {badge.badge_class_id.issuer_id.name}")
        _logger.info(f"Public Key Exists: {bool(badge.badge_class_id.issuer_id.public_key)}")

        if badge.verification_type == 'SignedBadge':
            assertion_data = badge.get_json_ld()
            _logger.info(f"Assertion Data: {assertion_data}")
            signature = assertion_data.get('signature')
            _logger.info(f"Signature Exists: {bool(signature)}")
            
            public_key = badge.badge_class_id.issuer_id.public_key
            if not signature or not public_key:
                _logger.error("Missing signature or public key")
                _logger.error(f"Signature: {signature}")
                _logger.error(f"Public Key: {public_key}")
        
        if not badge:
            return request.render('ak_open_badges.verification_error', {
                'error': 'Invalid verification token'
            })

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
                verification_status['messages'].append('Certificate verification failed: Missing digital signature or issuer key.')
            elif not self._verify_signature(assertion_data, signature, public_key):
                verification_status['is_valid'] = False
                verification_status['messages'].append('Certificate verification failed: Invalid digital signature. The certificate may have been modified.')

        # Süre kontrolü
        if badge.expiration_date and badge.expiration_date < fields.Datetime.now():
            verification_status['is_valid'] = False
            verification_status['messages'].append('Badge has expired')

        # İptal kontrolü
        if badge.state == 'revoked':
            verification_status['is_valid'] = False
            verification_status['messages'].append('Badge has been revoked')
            
         # Eğer doğrulama başarısızsa, hata sayfasını göster
        if not verification_status['is_valid']:
            return request.render('ak_open_badges.verification_error', {
                'error': ' '.join(verification_status['messages'])
            })

        # Certificate data'yı base64 formatında template'e gönder
        certificate_data = False
        if badge.certificate_file:
            certificate_data = badge.certificate_file.decode('utf-8')

        return request.render('ak_open_badges.verification_page', {
            'badge': badge,
            'data': verification_data,
            'verification': verification_status,
            'certificate_data': certificate_data
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
        
        

        