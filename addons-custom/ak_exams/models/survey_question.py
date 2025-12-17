# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
import itertools

class SurveyQuestion(models.Model):
    _inherit = 'survey.question'
    
    category_id = fields.Many2one(
        'survey.question.poll.category',
        string=_('Category'),
        tracking=True
    )
    
    # Randomization fields  
    is_mandatory = fields.Boolean(string='Zorunlu Soru', default=False)
    question_group = fields.Char(string='Soru Grubu')
    
    def get_randomized_suggested_answers(self, user_input_id):
        """Get randomized suggested answers for this question"""
        return self.survey_id._get_randomized_suggested_answers(self, user_input_id)
    
    @api.onchange('survey_id')
    def _onchange_survey_id(self):
        """Update domain of category_id based on survey_id"""
        if self.survey_id and self.survey_id.company_id:
            return {'domain': {'category_id': ['|', ('company_id', '=', False), ('company_id', '=', self.survey_id.company_id.id)]}}
        return {'domain': {'category_id': []}}

    def _get_stats_graph_data_matrix(self, user_input_lines):
        """
        Override to prevent KeyError when user_input_lines contain answers
        not corresponding to the current question's matrix_row_id or suggested_answer_id.
        """
        self.ensure_one() # Ensure self is a single record
        suggested_answers = self.mapped('suggested_answer_ids')
        matrix_rows = self.mapped('matrix_row_ids')

        # Initialize count_data with all possible combinations for this question
        count_data = dict.fromkeys(itertools.product(matrix_rows, suggested_answers), 0)

        for line in user_input_lines:
            # Ensure the line's row and answer IDs are part of the current question's configuration
            if line.matrix_row_id and line.suggested_answer_id:
                key = (line.matrix_row_id, line.suggested_answer_id)
                # Only increment if the key (combination of row and answer) is valid for this question
                if key in count_data:
                    count_data[key] += 1

        table_data = [{
            'row': row,
            'columns': [{
                'suggested_answer': suggested_answer,
                'count': count_data.get((row, suggested_answer), 0) # Use .get for safety, though key should exist
            } for suggested_answer in suggested_answers],
        } for row in matrix_rows]

        graph_data = [{
            'key': suggested_answer.value,
            'values': [{
                'text': row.value,
                'count': count_data.get((row, suggested_answer), 0) # Use .get for safety
            } for row in matrix_rows]
        } for suggested_answer in suggested_answers]

        return table_data, graph_data