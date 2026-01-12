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
    
    def action_reset_to_new(self):
        """Reset selected survey inputs to 'new' state so participants can retake the exam"""
        for record in self:
            record.write({
                'state': 'new',
                'start_datetime': False,
                'end_datetime': False,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Başarılı',
                'message': f'{len(self)} katılımcı "Yeni" durumuna alındı. Artık sınava tekrar girebilirler.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_set_to_in_progress(self):
        """Set selected survey inputs to 'in_progress' state"""
        for record in self:
            record.write({
                'state': 'in_progress',
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Başarılı',
                'message': f'{len(self)} katılımcı "İşlemde" durumuna alındı.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.model_create_multi
    def create(self, vals_list):
        _logger.info(f"=== SurveyUserInput.create CALLED with {len(vals_list)} records ===")
        for i, vals in enumerate(vals_list):
            _logger.info(f"Record {i}: survey_id={vals.get('survey_id')}, partner_id={vals.get('partner_id')}")
            # Randomize answer order for each question
            if 'randomized_answer_order' not in vals:
                survey_id = vals.get('survey_id', self.env.context.get('default_survey_id'))
                _logger.info(f"Survey ID: {survey_id}")
                if survey_id:
                    survey = self.env['survey.survey'].browse(survey_id)
                    _logger.info(f"Survey found: {survey.title}")
                    randomized_order = {}
                    for question in survey.question_ids.filtered(lambda q: q.question_type in ['simple_choice', 'multiple_choice']):
                        answer_ids = question.suggested_answer_ids.ids
                        random.shuffle(answer_ids)
                        randomized_order[str(question.id)] = answer_ids
                        _logger.info(f"Question {question.id} randomized answers: {answer_ids}")
                    vals['randomized_answer_order'] = randomized_order
                    _logger.info(f"Final randomized_answer_order: {randomized_order}")
        result = super().create(vals_list)
        _logger.info(f"=== SurveyUserInput.create COMPLETED, created {len(result)} records ===")
        return result