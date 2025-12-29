# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError
import logging
import time
import json

_logger = logging.getLogger(__name__)

try:
    import anthropic
except ImportError:
    anthropic = None


class AkAiServiceAnthropic(models.Model):
    _name = 'ak_ai.service.anthropic'
    _inherit = 'ak_ai.service'
    _description = 'Anthropic Claude Service'

    @api.model
    def get_available_models(self, provider=None):
        """Get available Anthropic models - Anthropic doesn't have a models API,
        so we maintain a curated list of available models"""
        return [
            # Claude 4 family (latest)
            ('claude-opus-4-20250514', 'Claude Opus 4 (200k context)'),
            ('claude-sonnet-4-20250514', 'Claude Sonnet 4 (200k context)'),
            
            # Claude 3.5 family
            ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet (200k context)'),
            ('claude-3-5-haiku-20241022', 'Claude 3.5 Haiku (200k context)'),
            
            # Claude 3 family
            ('claude-3-opus-20240229', 'Claude 3 Opus (200k context)'),
            ('claude-3-sonnet-20240229', 'Claude 3 Sonnet (200k context)'),
            ('claude-3-haiku-20240307', 'Claude 3 Haiku (200k context)'),
            
            # Custom option
            ('custom', 'Custom Model (Enter Below)'),
        ]

    def generate_response(self, user_message, context):
        """Generate response using Anthropic Claude"""
        if not anthropic:
            raise ValidationError(_('Anthropic library not installed. Run: pip install anthropic'))
        
        assistant = self.env['ak_ai.assistant'].get_active_assistant()
        
        if not assistant.api_key:
            raise ValidationError(_('Anthropic API key not configured'))
        
        start_time = time.time()
        
        try:
            # Configure Anthropic
            client = anthropic.Anthropic(
                api_key=assistant.api_key,
                base_url=assistant.api_base_url or None
            )
            
            # Build messages
            messages = self._build_messages(user_message, context)
            system_prompt = self._build_system_prompt(context)
            
            # Call Anthropic API
            response = client.messages.create(
                model=assistant.get_model_name(),
                max_tokens=assistant.max_tokens,
                temperature=assistant.temperature,
                system=system_prompt,
                messages=messages
            )
            
            ai_response = response.content[0].text
            
            # Extract token usage
            tokens_input = response.usage.input_tokens if response.usage else 0
            tokens_output = response.usage.output_tokens if response.usage else 0
            tokens_used = tokens_input + tokens_output
            
            # Anthropic doesn't provide cost in the response object directly
            cost = 0.0
            
            response_time = time.time() - start_time
            
            # Validate response for security
            self._validate_response(ai_response)
            
            # Log interaction
            self._log_interaction(
                user_message, ai_response, context, 
                tokens_used=tokens_used, 
                response_time=response_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost=cost
            )
            
            return ai_response
            
        except Exception as e:
            _logger.error(f"Anthropic API error: {e}")
            return _('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.')
    
    def _build_messages(self, user_message, context):
        """Build message array for Anthropic (no system role in messages)"""
        messages = []
        
        # Conversation history (no system messages)
        history = context.get('messages', [])
        for msg in history[-5:]:  # Last 5 messages
            if msg['role'] != 'system':  # Anthropic handles system separately
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        # Current user message
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        return messages