from odoo import models, fields, _


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    slide_category = fields.Selection(
        selection_add=[('report', _('Reports'))]
    )
    