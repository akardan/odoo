# -*- coding: utf-8 -*-

from odoo import models, fields, _


class Survey(models.Model):
    _inherit = 'survey.survey'
    
    company_id = fields.Many2one(
        'res.company', 
        string=_('Company'),
        default=lambda self: self.env.company
    )

    def _can_go_back(self, answer, page_or_question):
        self.ensure_one()
        if self.questions_layout == "one_page" or not self.users_can_go_back:
            return False
        if answer.state != 'in_progress' or answer.is_session_answer:
            return False

        # Determine the list of questions/pages relevant for navigation
        if self.questions_layout == 'page_per_section':
            # For 'page_per_section', navigation is based on survey.page_ids
            if self.page_ids and page_or_question == self.page_ids[0]:
                return False
            return True # Can go back if not first page
        else: # 'page_per_question'
            # For 'page_per_question', navigation is based on question_ids
            # Use predefined_question_ids if random, otherwise survey.question_ids
            if not answer.is_session_answer and self.questions_selection == 'random':
                relevant_questions = answer.predefined_question_ids
            else:
                relevant_questions = self.question_ids

            if relevant_questions and page_or_question == relevant_questions[0]:
                return False
            return True # Can go back if not first question in the relevant list

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='survey_id.company_id',
        store=True,
        readonly=True
    )
