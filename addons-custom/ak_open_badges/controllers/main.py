from odoo import http ,_
from odoo.http import request
import json

class OpenBadgesController(http.Controller):
    
    @http.route(['/badge/verify/<string:token>'], type='http', auth='public', website=True)
    def verify_badge(self, token):
        """Rozet doğrulama sayfası"""
        Badge = request.env['badge.assertion'].sudo()
        badge = Badge.search([('assertion_url', 'like', f'%{token}')], limit=1)
        
        if not badge:
            return request.render('ak_open_badges.verification_error', {
                'error': _('Invalid verification token')
            })
            
        verification_data = badge.get_verification_data()
        return request.render('ak_open_badges.verification_page', {
            'badge': badge,
            'data': verification_data
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