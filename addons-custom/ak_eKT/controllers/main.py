from odoo import http
from odoo.http import request
import json
from datetime import datetime

class DigitalProspectusController(http.Controller):

    @http.route('/ekt/<string:unique_code>', type='http', auth='public', website=True)
    def view_prospectus(self, unique_code, lang='tr', **kwargs):
        """Herkese açık prospektüs görüntüleme"""
        prospectus = request.env['digital.prospectus'].sudo().search([
            ('unique_code', '=', unique_code),
            ('state', '=', 'published')
        ], limit=1)
        
        if not prospectus:
            return request.render('http_routing.404')
        
        # Görüntülenme sayısını artır
        user_info = {
            'ip': request.httprequest.remote_addr,
            'user_agent': request.httprequest.headers.get('User-Agent', '')
        }
        prospectus.increment_view_count(user_info)
        
        # Dil seçimi
        content_field = f'content_{lang}' if hasattr(prospectus, f'content_{lang}') else 'content_turkish'
        audio_field = f'audio_{lang}' if hasattr(prospectus, f'audio_{lang}') else 'audio_turkish'
        
        values = {
            'prospectus': prospectus,
            'content': getattr(prospectus, content_field, prospectus.content_turkish),
            'audio': getattr(prospectus, audio_field, prospectus.audio_turkish),
            'current_lang': lang,
            'available_languages': ['tr', 'en', 'ar']  # Türkçe, İngilizce, Arapça
        }
        
        return request.render('ak_eKT.prospectus_public_view', values)
    
    @http.route('/ekt/download/<string:unique_code>', type='http', auth='public')
    def download_prospectus(self, unique_code, format='pdf', **kwargs):
        """Prospektüs indirme"""
        prospectus = request.env['digital.prospectus'].sudo().search([
            ('unique_code', '=', unique_code),
            ('state', '=', 'published')
        ], limit=1)
        
        if not prospectus:
            return request.not_found()
        
        # İndirme sayısını artır
        prospectus.download_count += 1
        request.env['prospectus.usage.analytics'].sudo().create({
            'prospectus_id': prospectus.id,
            'action': 'download',
            'user_ip': request.httprequest.remote_addr,
            'user_agent': request.httprequest.headers.get('User-Agent', ''),
            'access_date': datetime.now()
        })
        
        if format == 'pdf':
            # PDF oluşturma (wkhtmltopdf kullanarak)
            pdf_content = request.env.ref('ak_eKT.prospectus_pdf_report')._render_qweb_pdf([prospectus.id])[0]
            
            response = request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', f'attachment; filename="{prospectus.product_id.name}_prospektus.pdf"')
                ]
            )
            return response
    
    @http.route('/ekt/analytics', type='json', auth='public', methods=['POST'])
    def track_usage(self, unique_code, action, **kwargs):
        """Kullanım analitiği için AJAX endpoint"""
        prospectus = request.env['digital.prospectus'].sudo().search([
            ('unique_code', '=', unique_code)
        ], limit=1)
        
        if prospectus:
            request.env['prospectus.usage.analytics'].sudo().create({
                'prospectus_id': prospectus.id,
                'action': action,
                'user_ip': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
                'language': kwargs.get('language', 'tr'),
                'access_date': datetime.now()
            })
            
        return {'status': 'success'}