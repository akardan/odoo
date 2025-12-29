# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AkAiLearning(models.Model):
    _name = 'ak_ai.learning'
    _description = 'AI Learning & Feedback'
    _order = 'create_date desc'

    message_id = fields.Many2one('ak_ai.message', 'Message', required=True, ondelete='cascade')
    conversation_id = fields.Many2one('ak_ai.conversation', 'Conversation', required=True)
    user_id = fields.Many2one('res.users', 'User', required=True)
    
    rating = fields.Selection([
        ('1', 'Very Bad'),
        ('2', 'Bad'), 
        ('3', 'Neutral'),
        ('4', 'Good'),
        ('5', 'Excellent'),
    ], string='Rating', required=True)
    
    feedback_text = fields.Text('Feedback')
    
    # Context for learning
    context_model = fields.Char('Context Model')
    context_res_id = fields.Integer('Context Record ID')
    
    # Learning categories
    category = fields.Selection([
        ('accuracy', 'Response Accuracy'),
        ('helpfulness', 'Helpfulness'),
        ('security', 'Security Compliance'),
        ('performance', 'Performance'),
        ('other', 'Other'),
    ], string='Feedback Category', default='helpfulness')
    
    processed = fields.Boolean('Processed for Learning', default=False)
    
    @api.model
    def get_learning_insights(self):
        """Get insights for AI improvement"""
        insights = {}
        
        # Rating distribution
        ratings = self.read_group(
            [], ['rating'], ['rating']
        )
        insights['ratings'] = {r['rating']: r['rating_count'] for r in ratings}
        
        # Common feedback themes
        negative_feedback = self.search([('rating', 'in', ['1', '2'])])
        insights['improvement_areas'] = negative_feedback.mapped('category')
        
        return insights