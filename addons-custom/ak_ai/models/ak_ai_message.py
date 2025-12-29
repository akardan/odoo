# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AkAiMessage(models.Model):
    _name = 'ak_ai.message'
    _description = 'AI Conversation Message'
    _order = 'create_date asc'
    _rec_name = 'content'

    conversation_id = fields.Many2one('ak_ai.conversation', 'Conversation', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.user)
    
    content = fields.Text('Content', required=True)
    message_type = fields.Selection([
        ('user', 'User Message'),
        ('assistant', 'Assistant Response'),
        ('system', 'System Message'),
    ], string='Type', required=True)
    
    # AI Response Details
    ai_model = fields.Char('AI Model Used')
    tokens_used = fields.Integer('Tokens Used')
    response_time = fields.Float('Response Time (seconds)')
    
    # User Feedback
    rating = fields.Selection([
        ('1', 'Very Bad'),
        ('2', 'Bad'),
        ('3', 'Neutral'),
        ('4', 'Good'),
        ('5', 'Excellent'),
    ], string='User Rating')
    
    feedback_text = fields.Text('User Feedback')
    is_helpful = fields.Boolean('Marked as Helpful')
    
    # Error Handling
    error_details = fields.Text('Error Details')
    retry_count = fields.Integer('Retry Count', default=0)
    
    # Audit Trail
    ip_address = fields.Char('IP Address')
    user_agent = fields.Char('User Agent')
    
    def rate_message(self, rating, feedback_text=None):
        """Rate AI message - user can only rate their own conversations"""
        if self.conversation_id.user_id != self.env.user:
            raise AccessError(_('You can only rate messages in your own conversations'))
            
        self.write({
            'rating': rating,
            'feedback_text': feedback_text,
            'is_helpful': rating in ['4', '5'],
        })
        
        # Log feedback for learning
        self._log_feedback()
    
    def _log_feedback(self):
        """Log feedback for AI learning system"""
        try:
            self.env['ak_ai.learning'].create({
                'message_id': self.id,
                'conversation_id': self.conversation_id.id,
                'user_id': self.user_id.id,
                'rating': self.rating,
                'feedback_text': self.feedback_text,
                'context_model': self.conversation_id.context_model,
                'context_res_id': self.conversation_id.context_res_id,
            })
        except Exception as e:
            _logger.error(f"Error logging feedback: {e}")
    
    @api.model
    def create(self, vals):
        """Override create to add audit info"""
        
        # Add audit information
        request = self.env.context.get('request')
        if request:
            vals.update({
                'ip_address': request.httprequest.environ.get('REMOTE_ADDR'),
                'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
            })
        
        return super().create(vals)