# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class AkAiAssistant(models.Model):
    _name = 'ak_ai.assistant'
    _description = 'KAI Assistant Configuration'
    _rec_name = 'name'

    name = fields.Char('Assistant Name', default='KAI', required=True)
    active = fields.Boolean('Active', default=True)
    
    # AI Service Configuration
    ai_provider = fields.Selection([
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('openrouter', 'OpenRouter'),
        ('local', 'Local LLM'),
    ], string='AI Provider', default='openrouter', required=True)
    
    # Simple Char field for model name - user can type any model
    model_name = fields.Char('Model Name', required=True, help="Enter the model ID. Examples: gpt-4o-mini, claude-3-5-haiku-20241022, anthropic/claude-3.5-haiku")
    
    api_key = fields.Char('API Key', groups='base.group_system')
    api_base_url = fields.Char('API Base URL')
    
    # Security Settings
    max_tokens = fields.Integer('Max Tokens', default=4000, help="Maximum tokens for AI response. Increase if responses are being cut off. Most models support 4000-8000 output tokens.")
    temperature = fields.Float('Temperature', default=0.3, help="Controls randomness (0.0-1.0). Lower values (0.2-0.3) are better for code generation, higher values (0.7-0.9) for creative tasks.")
    rate_limit_per_user = fields.Integer('Rate Limit (per user/hour)', default=100)
    
    # Knowledge Settings
    enable_learning = fields.Boolean('Enable Learning', default=True)
    knowledge_retention_days = fields.Integer('Knowledge Retention (days)', default=365)
    
    # User Access
    allowed_user_ids = fields.Many2many('res.users', string='Allowed Users')
    allowed_group_ids = fields.Many2many('res.groups', string='Allowed Groups')
    
    
    @api.onchange('ai_provider')
    def _onchange_ai_provider(self):
        """Reset model_name when provider changes"""
        if self.ai_provider:
            # Set default model based on provider
            default_models = {
                'openai': 'gpt-4o-mini',
                'anthropic': 'claude-3-5-sonnet-20241022',
                'openrouter': 'anthropic/claude-3.5-haiku',
                'local': 'llama-3.2',
            }
            self.model_name = default_models.get(self.ai_provider, False)
            
            # Set default API base URL
            default_urls = {
                'openai': 'https://api.openai.com/v1',
                'anthropic': 'https://api.anthropic.com',
                'openrouter': 'https://openrouter.ai/api/v1',
                'local': 'http://localhost:11434/v1',
            }
            if not self.api_base_url:
                self.api_base_url = default_urls.get(self.ai_provider, '')
    
    @api.onchange('model_name')
    def _onchange_model_name(self):
        """Show/hide custom model name field"""
        if self.model_name == 'custom':
            return {
                'warning': {
                    'title': _('Custom Model'),
                    'message': _('Please enter the custom model name in the field below.')
                }
            }
    
    def get_model_name(self):
        """Get the actual model name to use"""
        self.ensure_one()
        return self.model_name or 'gpt-4o-mini'
    
    @api.model
    def get_active_assistant(self):
        """Get the active assistant configuration"""
        assistant = self.search([('active', '=', True)], limit=1)
        if not assistant:
            raise ValidationError(_('No active AI assistant configured. Please configure KAI first.'))
        return assistant
    
    def check_user_access(self, user_id=None):
        """Check if user has access to AI assistant - respects user permissions"""
        if not user_id:
            user_id = self.env.user.id
            
        user = self.env['res.users'].browse(user_id)
        
        # Check if user has KAI User group
        kai_user_group = self.env.ref('ak_ai.group_ak_ai_user', raise_if_not_found=False)
        if kai_user_group and kai_user_group not in user.groups_id:
            # If group exists and user doesn't have it, deny access
            return False
        
        # Check if user is in allowed users
        if self.allowed_user_ids and user not in self.allowed_user_ids:
            return False
            
        # Check if user has any allowed groups
        if self.allowed_group_ids:
            user_groups = user.groups_id
            if not any(group in user_groups for group in self.allowed_group_ids):
                return False
                
        return True
    
    def get_user_context(self, user_id=None):
        """Get user context for AI - only data user has access to"""
        if not user_id:
            user_id = self.env.user.id
            
        user = self.env['res.users'].browse(user_id)
        
        # Only return data the user has access to
        context = {
            'user': {
                'id': user.id,
                'name': user.name,
                'login': user.login,
                'lang': user.lang,
                'tz': user.tz,
                'company_id': user.company_id.id,
                'company_name': user.company_id.name,
            },
            'permissions': self._get_user_permissions(user),
            'preferences': self._get_user_preferences(user),
        }
        
        return context
    
    def _get_user_permissions(self, user):
        """Get user permissions - what they can actually do"""
        permissions = {}
        
        # Check common model permissions
        models_to_check = [
            'sale.order', 'purchase.order', 'account.move',
            'res.partner', 'product.product', 'stock.picking'
        ]
        
        for model_name in models_to_check:
            try:
                model = self.env[model_name]
                permissions[model_name] = {
                    'read': model.check_access_rights('read', raise_exception=False),
                    'create': model.check_access_rights('create', raise_exception=False),
                    'write': model.check_access_rights('write', raise_exception=False),
                    'unlink': model.check_access_rights('unlink', raise_exception=False),
                }
            except KeyError:
                # Model doesn't exist
                continue
                
        return permissions
    
    def _get_user_preferences(self, user):
        """Get user preferences and settings"""
        return {
            'language': user.lang,
            'timezone': user.tz,
            'date_format': '%d/%m/%Y',
            'currency': user.company_id.currency_id.name,
        }
    
    @api.model
    def create_default_assistant(self):
        """Create default assistant configuration"""
        if not self.search([]):
            self.create({
                'name': 'KAI',
                'ai_provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'max_tokens': 4000,
                'temperature': 0.3,
                'rate_limit_per_user': 100,
                'enable_learning': True,
                'knowledge_retention_days': 365,
            })