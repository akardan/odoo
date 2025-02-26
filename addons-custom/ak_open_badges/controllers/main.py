from odoo import http, _, fields
from odoo.http import request
import json
from cryptography.exceptions import InvalidSignature
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from io import BytesIO
from cryptography.hazmat.primitives.asymmetric import padding
import logging
from werkzeug.urls import url_encode
from pdf2image import convert_from_bytes
from urllib.parse import quote_plus


_logger = logging.getLogger(__name__)

class OpenBadgesController(http.Controller):
    
    def _verify_signature(self, assertion_data, signature, public_key_pem):
        """Rozet imzasını doğrula"""
        try:
            # Debug log ekleyelim
            # _logger.info("=== Signature Verification Debug ===")
            # _logger.info(f"Assertion Data Type: {type(assertion_data)}")
            # _logger.info(f"Signature Type: {type(signature)}")

            # Public key'i yükle
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # JSON verisini string'e çevir (signature hariç)
            assertion_copy = assertion_data.copy()
            assertion_copy.pop('signature', None)
            assertion_string = json.dumps(assertion_copy, sort_keys=True)

            # _logger.info(f"Data to verify: {assertion_string}")

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
                # _logger.info("Signature verification successful!")
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

        if not badge:
            return request.render('ak_open_badges.verification_error', {
                'error': 'Invalid verification token'
            })
            
        if badge.verification_type == 'SignedBadge':
            assertion_data = badge.get_json_ld()
            # _logger.info(f"Assertion Data: {assertion_data}")
            signature = assertion_data.get('signature')
            # _logger.info(f"Signature Exists: {bool(signature)}")
            
            public_key = badge.badge_class_id.issuer_id.public_key
            if not signature or not public_key:
                _logger.error("Missing signature or public key")
                _logger.error(f"Signature: {signature}")
                _logger.error(f"Public Key: {public_key}")
        

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

        # # Certificate data'yı base64 formatında hazırla
        certificate_data = False
        pdf_url = False
        if badge.certificate_file:
            certificate_data = badge.certificate_file.decode('utf-8')
        
        # PDF'i resme çevir
        try:
            pdf_bytes = base64.b64decode(certificate_data)
            pages = convert_from_bytes(pdf_bytes, dpi=200)  # DPI kaliteyi ayarlar
            if pages:
                img_byte_arr = BytesIO()
                pages[0].save(img_byte_arr, format='PNG', optimize=True, quality=85)
                certificate_image = base64.b64encode(img_byte_arr.getvalue()).decode()
        except Exception as e:
            _logger.error(f"PDF to image conversion error: {e}")


        # Alignment verilerini hazırla
        alignment_data = []
        for align in badge.badge_class_id.alignment:
            align_data = {
                'target_name_primary': align.with_context(lang=badge.badge_class_id.primary_lang).sudo().target_name,
                'target_name_secondary': align.with_context(lang=badge.badge_class_id.secondary_lang).sudo().target_name,
                'target_description_primary': align.with_context(lang=badge.badge_class_id.primary_lang).sudo().target_description,
                'target_description_secondary': align.with_context(lang=badge.badge_class_id.secondary_lang).sudo().target_description,
                'target_framework_primary': align.with_context(lang=badge.badge_class_id.primary_lang).sudo().target_framework,
                'target_framework_secondary': align.with_context(lang=badge.badge_class_id.secondary_lang).sudo().target_framework,
                'target_code': align.target_code,
                'target_url': align.target_url
            }
            alignment_data.append(align_data)

        # Evidence verilerini hazırla
        evidence_data = []
        for evidence in badge.evidence:
            # Her bir evidence için çift dil desteği
            if evidence:  # evidence kaydının var olduğunu kontrol et
                ev_data = {
                    'name_primary': evidence.with_context(lang=badge.badge_class_id.primary_lang).sudo().name or '',
                    'name_secondary': evidence.with_context(lang=badge.badge_class_id.secondary_lang).sudo().name or '',
                    'description_primary': evidence.with_context(lang=badge.badge_class_id.primary_lang).sudo().description or '',
                    'description_secondary': evidence.with_context(lang=badge.badge_class_id.secondary_lang).sudo().description or '',
                    'genre_primary': evidence.with_context(lang=badge.badge_class_id.primary_lang).sudo().genre or '',
                    'genre_secondary': evidence.with_context(lang=badge.badge_class_id.secondary_lang).sudo().genre or '',
                    'narrative_primary': evidence.with_context(lang=badge.badge_class_id.primary_lang).sudo().narrative or '',
                    'narrative_secondary': evidence.with_context(lang=badge.badge_class_id.secondary_lang).sudo().narrative or '',
                    'audience_primary': evidence.with_context(lang=badge.badge_class_id.primary_lang).sudo().audience or '',
                    'audience_secondary': evidence.with_context(lang=badge.badge_class_id.secondary_lang).sudo().audience or '',
                    'type_primary': evidence.with_context(lang=badge.badge_class_id.primary_lang).sudo().type or 'Evidence',
                    'type_secondary': evidence.with_context(lang=badge.badge_class_id.secondary_lang).sudo().type or 'Evidence'
                }
                evidence_data.append(ev_data)

        # Evidence verisi var mı kontrol et
        if not evidence_data:
            evidence_data = None
            
         # Increment the verify count
        badge.sudo().write({'verify_count': badge.verify_count + 1})
       
        return request.render('ak_open_badges.verification_page', {
            'badge': badge,
            'data': verification_data,
            'verification': verification_status,
            'certificate_data': certificate_data,
            'alignment_data' : alignment_data,
            'evidence_data': evidence_data,
            'certificate_image': certificate_image,
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
        
        

        