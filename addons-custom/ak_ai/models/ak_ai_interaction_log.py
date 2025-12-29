# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class AkAiInteractionLog(models.Model):
    _name = 'ak_ai.interaction_log'
    _description = 'AI Interaction Log'
    _order = 'create_date desc'
    _rec_name = 'user_message'

    user_id = fields.Many2one('res.users', 'User', required=True, index=True)
    user_message = fields.Text('User Message', required=True)
    ai_response = fields.Text('AI Response', required=True)
    
    context_data = fields.Text('Context Data (JSON)')
    tokens_used = fields.Integer('Tokens Used', default=0)
    tokens_input = fields.Integer('Input Tokens', default=0)
    tokens_output = fields.Integer('Output Tokens', default=0)
    cost = fields.Float('Cost', digits=(12, 6), default=0.0)
    response_time = fields.Float('Response Time (seconds)', default=0.0)
    
    ai_provider = fields.Selection([
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('openrouter', 'OpenRouter'),
        ('local', 'Local LLM'),
        ('system', 'System'),
    ], string='AI Provider', required=True)
    
    model_name = fields.Char('AI Model')
    
    # Audit fields
    ip_address = fields.Char('IP Address')
    user_agent = fields.Char('User Agent')
    
    @api.model
    def cleanup_old_logs(self, days=90):
        """Clean up old interaction logs"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([('create_date', '<', cutoff_date)])
        old_logs.unlink()
        _logger.info(f"Cleaned up {len(old_logs)} old interaction logs")