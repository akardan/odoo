from odoo import models, fields, _


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
                    
