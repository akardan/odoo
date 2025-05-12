# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging
import json
import random

_logger = logging.getLogger(__name__)

class SurveyShuffleController(http.Controller):
    
    @http.route('/survey/get_shuffle_config', type='json', auth="public", website=True)
    def get_shuffle_config(self, survey_token, answer_token, **kwargs):
        """Return configuration about question shuffling for the survey"""
        try:
            survey_sudo, answer_sudo = self._get_survey_and_answer(survey_token, answer_token)
            
            if not survey_sudo or not answer_sudo:
                return {'shuffle_questions': False}
                
            return {
                'shuffle_questions': survey_sudo.shuffle_questions,
                'questions_layout': survey_sudo.questions_layout
            }
        except Exception as e:
            _logger.error("Error in get_shuffle_config: %s", str(e))
            return {'shuffle_questions': False}
            
    def _get_survey_and_answer(self, survey_token, answer_token):
        """Helper to get survey and answer records from tokens"""
        # Based on Odoo's survey controller code
        survey_sudo = request.env['survey.survey'].with_context(active_test=False).sudo().search([('access_token', '=', survey_token)])
        if not answer_token:
            answer_sudo = request.env['survey.user_input'].sudo()
        else:
            answer_sudo = request.env['survey.user_input'].sudo().search([
                ('survey_id', '=', survey_sudo.id),
                ('access_token', '=', answer_token)
            ], limit=1)
        return survey_sudo, answer_sudo