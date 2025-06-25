# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.tools.translate import _

class SurveyQuestionPollCategory(models.Model):
    _name = 'survey.question.poll.category'
    _description = 'Survey Question Poll Category'
    _order = 'sequence, name'

    name = fields.Char(string=_('Category Name'), required=True, translate=True)
    sequence = fields.Integer(string=_('Sequence'), default=10)
    company_id = fields.Many2one(
        'res.company', string=_('Company'),
        default=lambda self: self.env.company,
        help=_("If a company is set, the category is company-specific. Otherwise, it's a global category.")
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_company_uniq', 'unique (name, company_id)', _('Category name must be unique per company (or globally if no company is set)!'))
    ]