# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _

class SurveyCategoryQuestionCount(models.Model):
    _name = 'survey.category.question.count'
    _description = 'Exam Category Question Count Settings'

    survey_id = fields.Many2one('survey.survey', string=_('Exam'), required=True, ondelete='cascade')
    category_id = fields.Many2one('survey.question.poll.category', string=_('Category'), required=True)
    total_questions = fields.Integer(string=_('Total Questions'), readonly=True, compute='_compute_total_questions')
    questions_to_ask = fields.Integer(string=_('Questions to Ask'), default=0)

    @api.depends('survey_id', 'category_id')
    def _compute_total_questions(self):
        for record in self:
            if record.survey_id and record.category_id:
                count = self.env['survey.question'].search_count([
                    ('survey_id', '=', record.survey_id.id),
                    ('category_id', '=', record.category_id.id)
                ])
                record.total_questions = count
            else:
                record.total_questions = 0

    _sql_constraints = [
        ('unique_survey_category', 'unique(survey_id, category_id)', 
         _('Each category can only have one question count setting per survey.'))
    ]