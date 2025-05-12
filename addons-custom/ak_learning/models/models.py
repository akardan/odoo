# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import random
import logging

_logger = logging.getLogger(__name__)

class Survey(models.Model):
    _inherit = 'survey.survey'
    
    shuffle_questions = fields.Boolean('Shuffled Question Order', 
        help='If checked, questions will be displayed in a random order for each user.')
    
    def _prepare_user_input_predefined_questions(self):
        """ Will generate the questions for a new user input.
            If shuffle_questions is enabled, the order of questions will be randomized.
        """
        # Get predefined questions using standard behavior
        questions = super()._prepare_user_input_predefined_questions()
        
        # If shuffle_questions is enabled, shuffle the questions
        if self.shuffle_questions and questions and len(questions) > 1:
            try:
                # Get a list of question IDs
                question_ids = questions.ids
                
                # Log original order for debugging
                _logger.info("Original question order: %s", question_ids)
                
                # Using shuffle algorithm to randomize
                random.shuffle(question_ids)
                
                # Log shuffled order
                _logger.info("Shuffled question order: %s", question_ids)
                
                # Return questions in shuffled order
                return self.env['survey.question'].browse(question_ids)
            except Exception as e:
                _logger.error("Error shuffling questions: %s", str(e))
                return questions
        
        return questions