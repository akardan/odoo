# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AkAiKnowledgeBuilder(models.Model):
    _name = 'ak_ai.knowledge_builder'
    _description = 'AI Knowledge Builder'
    _rec_name = 'title'

    title = fields.Char('Title', required=True)
    content = fields.Text('Content', required=True)
    
    # Knowledge categorization
    category = fields.Selection([
        ('odoo_help', 'Odoo Help'),
        ('business_process', 'Business Process'),
        ('technical', 'Technical'),
        ('faq', 'FAQ'),
        ('troubleshooting', 'Troubleshooting'),
    ], string='Category', default='odoo_help')
    
    # Context
    model_name = fields.Char('Related Model')
    tags = fields.Char('Tags (comma separated)')
    
    # Usage tracking
    usage_count = fields.Integer('Usage Count', default=0)
    last_used = fields.Datetime('Last Used')
    
    # Quality
    accuracy_score = fields.Float('Accuracy Score', default=0.0)
    user_rating = fields.Float('User Rating', default=0.0)
    
    active = fields.Boolean('Active', default=True)
    
    @api.model
    def search_knowledge(self, query, limit=5):
        """Search knowledge base for relevant content"""
        # Simple text search - can be enhanced with vector search
        domain = [
            ('active', '=', True),
            '|', '|',
            ('title', 'ilike', query),
            ('content', 'ilike', query),
            ('tags', 'ilike', query)
        ]
        
        results = self.search(domain, limit=limit, order='usage_count desc, accuracy_score desc')
        
        # Update usage stats
        results.write({
            'usage_count': fields.Integer('usage_count') + 1,
            'last_used': fields.Datetime.now()
        })
        
        return results