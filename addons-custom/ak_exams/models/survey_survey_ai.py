# -*- coding: utf-8 -*-

from odoo import models

class SurveySurvey(models.Model):
    _name = 'survey.survey'
    _inherit = ['survey.survey', 'ak_ai.mixin']
