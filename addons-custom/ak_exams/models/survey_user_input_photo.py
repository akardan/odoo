# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SurveyUserInputPhoto(models.Model):
    _name = 'survey.user_input.photo'
    _description = 'Survey User Input Photo Capture'
    _order = 'capture_datetime desc'
    
    # Relations
    user_input_id = fields.Many2one(
        'survey.user_input',
        string='Survey User Input',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Photo Data
    photo = fields.Binary(
        string='Photo',
        required=True,
        attachment=True  # Store in ir.attachment for better performance
    )
    photo_filename = fields.Char(
        string='Filename',
        compute='_compute_photo_filename',
        store=True
    )
    
    # Metadata
    capture_datetime = fields.Datetime(
        string='Capture Date/Time',
        required=True,
        default=fields.Datetime.now,
        index=True
    )
    capture_type = fields.Selection([
        ('initial', 'Initial Capture'),
        ('random', 'Random Capture'),
        ('manual', 'Manual Capture')
    ], string='Capture Type', required=True, default='random')
    
    # Technical Info
    browser_info = fields.Char(string='Browser Info')
    ip_address = fields.Char(string='IP Address')
    capture_success = fields.Boolean(string='Capture Success', default=True)
    error_message = fields.Text(string='Error Message')
    
    # Security
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='user_input_id.survey_id.company_id',
        store=True,
        index=True
    )
    
    @api.depends('user_input_id', 'capture_datetime')
    def _compute_photo_filename(self):
        for record in self:
            if record.user_input_id and record.capture_datetime:
                timestamp = record.capture_datetime.strftime('%Y%m%d_%H%M%S')
                record.photo_filename = f"exam_photo_{record.user_input_id.id}_{timestamp}.jpg"
            else:
                record.photo_filename = "exam_photo.jpg"
    
    def name_get(self):
        """Custom name for the record"""
        result = []
        for record in self:
            name = f"{record.capture_type.title()} - {record.capture_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
            result.append((record.id, name))
        return result
