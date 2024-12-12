from odoo import models, fields, _


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    slide_category = fields.Selection(
        selection_add=[('report', _('Reports'))],
        required=True,
        ondelete={'report': 'set default'},  # ondelete bir dict olarak tanımlandı
        default='document'  # önceden var olan bir seçenek varsayılan olarak kullanılabilir
    )    