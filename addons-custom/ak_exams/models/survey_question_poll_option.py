# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.tools.translate import _

class SurveyQuestionPollOption(models.Model):
    _name = 'survey.question.poll.option'
    _description = 'Survey Question Poll Option'
    _order = 'sequence, id'

    poll_id = fields.Many2one(
        'survey.question.poll',
        string=_('Poll'),
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string=_('Option Text'), required=True, translate=True)
    sequence = fields.Integer(string=_('Sequence'), default=10)
    is_correct = fields.Boolean(string=_('Is a Correct Answer?'), default=False)
    answer_score = fields.Float(string=_('Score for this Answer'), default=0.0)
    value_image = fields.Image(string=_('Image'), max_width=1024, max_height=1024)
    value_image_filename = fields.Char(string=_('Image Filename'))