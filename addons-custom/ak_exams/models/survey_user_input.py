from odoo import api, fields, models

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    ip_address = fields.Char(string='IP Address', readonly=True)
    randomized_question_ids = fields.Text(string="Randomized Question IDs", readonly=True)

    
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