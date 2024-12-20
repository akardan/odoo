from odoo import http
from odoo.http import request

class SlidesController4Tag(http.Controller):
    @http.route(['/slides/all'], type='http', auth='public', website=True)
    def course_slides_list(self, slide_category=None, **kwargs):
        domain = [('is_published', '=', True)]  # Yayınlanmış slide'ları getir

        # Eğer bir kategori varsa domain'e ekle
        if slide_category:
            domain.append(('category_id.name', '=', slide_category))

        # Gerekli veriler
        channels = request.env['slide.channel'].sudo().search([])
        slides = request.env['slide.slide'].sudo().search(domain)
        
        # İlk kanalı seçin veya bir varsayılan değer belirleyin
        channel = channels[0] if channels else None

        return request.render('website_slides.course_slides_list', {
            'channels': channels,
            'slides': slides,
            'channel': channel,  # Template'e channel gönderiliyor
            'selected_category': slide_category,
        })