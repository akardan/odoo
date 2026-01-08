from odoo import api, fields, models
import random
import logging

_logger = logging.getLogger(__name__)

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    ip_address = fields.Char(string='IP Address', readonly=True)
    randomized_question_ids = fields.Text(string="Randomized Question IDs", readonly=True)
    randomized_answer_order = fields.Json('Randomized Answer Order', help="Stores the randomized order of answers for each question")

    
    # Photo Capture Relations
    photo_ids = fields.One2many(
        'survey.user_input.photo',
        'user_input_id',
        string='Captured Photos'
    )
    photo_count = fields.Integer(
        string='Photo Count',
        compute='_compute_photo_count',
        store=True
    )
    camera_permission_granted = fields.Boolean(
        string='Camera Permission Granted',
        default=False
    )
    camera_permission_datetime = fields.Datetime(
        string='Camera Permission Date/Time'
    )
    
    @api.depends('photo_ids')
    def _compute_photo_count(self):
        for record in self:
            record.photo_count = len(record.photo_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        _logger.error(f"=== SurveyUserInput.create CALLED with {len(vals_list)} records ===")
        for i, vals in enumerate(vals_list):
            _logger.error(f"Record {i}: survey_id={vals.get('survey_id')}, partner_id={vals.get('partner_id')}")
            # Randomize answer order for each question
            if 'randomized_answer_order' not in vals:
                survey_id = vals.get('survey_id', self.env.context.get('default_survey_id'))
                _logger.error(f"Survey ID: {survey_id}")
                if survey_id:
                    survey = self.env['survey.survey'].browse(survey_id)
                    _logger.error(f"Survey found: {survey.title}")
                    randomized_order = {}
                    for question in survey.question_ids.filtered(lambda q: q.question_type in ['simple_choice', 'multiple_choice']):
                        answer_ids = question.suggested_answer_ids.ids
                        random.shuffle(answer_ids)
                        randomized_order[str(question.id)] = answer_ids
                        _logger.error(f"Question {question.id} randomized answers: {answer_ids}")
                    vals['randomized_answer_order'] = randomized_order
                    _logger.error(f"Final randomized_answer_order: {randomized_order}")
        result = super().create(vals_list)
        _logger.error(f"=== SurveyUserInput.create COMPLETED, created {len(result)} records ===")
        return result