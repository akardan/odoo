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
    
