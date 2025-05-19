# -*- coding: utf-8 -*-

from odoo import models, fields, _


class Survey(models.Model):
    _inherit = 'survey.survey'
    
    company_id = fields.Many2one(
        'res.company', 
        string=_('Company'),
        default=lambda self: self.env.company
    )

# class SurveyQuestion(models.Model):
#     _inherit = 'survey.question'
    
#     company_id = fields.Many2one(
#         'res.company', 
#         string='Company',
#         related='survey_id.company_id',  # Survey'den otomatik alınacak
#         store=True,  # Aramalar için depolanır
#         readonly=True  # Direkt düzenlenemez, survey'den gelir
#     )
