from odoo import models, fields, api, _
from odoo.http import request
from markupsafe import Markup


"""     Kurs objelerini genişletmek için kullanılan model.

"""
    
class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    nbr_report = fields.Integer("Number of Reports", compute='_compute_slides_statistics', store=True)    
    
    
class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    slide_category = fields.Selection(
        selection_add=[('report', _('Reports'))],
        required=True,
        ondelete={'report': 'set default'},  # ondelete bir dict olarak tanımlandı
        default='document'  # önceden var olan bir seçenek varsayılan olarak kullanılabilir
    )    
    nbr_report = fields.Integer("Number of Reports", compute="_compute_slides_statistics", store=True)
    
    def _compute_slide_type(self):
        super(SlideSlide, self)._compute_slide_type()
        for slide in self:
            if slide.slide_category == 'report':
                if slide.source_type == 'local_file':
                    slide.slide_type = 'pdf'
                elif slide.slide_type not in ['pdf', 'sheet', 'doc', 'slides']:
                    slide.slide_type = False
                    
    @api.depends('slide_category', 'google_drive_id', 'video_source_type', 'youtube_id')
    def _compute_embed_code(self):
        super(SlideSlide, self)._compute_embed_code()
        request_base_url = request.httprequest.url_root if request else False
        for slide in self:
            base_url = request_base_url or slide.get_base_url()
            if base_url[-1] == '/':
                base_url = base_url[:-1]
            
            if slide.slide_category == 'report':
                if slide.source_type == 'external' and slide.google_drive_id:
                    embed_code = Markup('<iframe src="//drive.google.com/file/d/%s/preview" allowFullScreen="true" frameborder="0" aria-label="%s"></iframe>') % (slide.google_drive_id, _('Google Drive'))
                elif slide.source_type == 'local_file':
                    slide_url = base_url + self.env['ir.http']._url_for('/slides/embed/%s?page=1' % slide.id)
                    slide_url_external = base_url + self.env['ir.http']._url_for('/slides/embed_external/%s?page=1' % slide.id)
                    base_embed_code = Markup('<iframe src="%s" class="o_wslides_iframe_viewer" allowFullScreen="true" height="%s" width="%s" frameborder="0" aria-label="%s"></iframe>')
                    iframe_aria_label = _('Embed code')
                    embed_code = base_embed_code % (slide_url, 315, 420, iframe_aria_label)
                    embed_code_external = base_embed_code % (slide_url_external, 315, 420, iframe_aria_label)

                slide.embed_code = embed_code
                slide.embed_code_external = embed_code_external or embed_code
