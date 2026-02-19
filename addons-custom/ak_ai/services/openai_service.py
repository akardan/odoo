# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError
import logging
import time
import json
from datetime import timedelta
import requests

_logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    openai = None


class AkAiServiceOpenAI(models.Model):
    _name = 'ak_ai.service.openai'
    _inherit = 'ak_ai.service'
    _description = 'OpenAI Service'

    @api.model
    def get_available_models(self, provider=None):
        """Get available OpenAI models from API"""
        models = []
        
        try:
            # Try to fetch from OpenAI API
            assistant = self.env['ak_ai.assistant'].search([('ai_provider', '=', 'openai')], limit=1)
            
            if assistant and assistant.api_key:
                headers = {
                    'Authorization': f'Bearer {assistant.api_key}'
                }
                
                base_url = assistant.api_base_url or 'https://api.openai.com/v1'
                response = requests.get(
                    f'{base_url}/models',
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Filter for chat models only
                    chat_models = []
                    for model in data.get('data', []):
                        model_id = model.get('id', '')
                        # Include GPT models for chat
                        if 'gpt' in model_id and any(x in model_id for x in ['3.5', '4', '4o']):
                            chat_models.append((model_id, model_id.upper()))
                    
                    # Sort by version (4o > 4 > 3.5)
                    chat_models.sort(key=lambda x: x[0], reverse=True)
                    models = chat_models[:10]  # Limit to 10
        except Exception as e:
            _logger.warning(f"Could not fetch OpenAI models from API: {e}")
        
        # Fallback to common models if API call failed
        if not models:
            models = [
                ('gpt-4o', 'GPT-4o'),
                ('gpt-4o-mini', 'GPT-4o Mini'),
                ('gpt-4-turbo', 'GPT-4 Turbo'),
                ('gpt-4', 'GPT-4'),
                ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
            ]
        
        # Add custom option
        models.append(('custom', 'Custom Model (Enter Below)'))
        
        return models

    def generate_response(self, user_message, context):
        """Generate response using OpenAI"""
        if not openai:
            raise ValidationError(_('OpenAI library not installed. Run: pip install openai'))
        
        assistant = self.env['ak_ai.assistant'].get_active_assistant()
        
        if not assistant.api_key:
            raise ValidationError(_('OpenAI API key not configured'))
        
        start_time = time.time()
        
        try:
            # Configure OpenAI
            client = openai.OpenAI(
                api_key=assistant.api_key,
                base_url=assistant.api_base_url or None
            )
            
            # Build messages
            messages = self._build_messages(user_message, context)
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=assistant.get_model_name(),
                messages=messages,
                max_tokens=assistant.max_tokens,
                temperature=assistant.temperature,
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract token usage
            tokens_input = response.usage.prompt_tokens if response.usage else 0
            tokens_output = response.usage.completion_tokens if response.usage else 0
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # OpenRouter provides cost in the response if using OpenRouter via OpenAI client
            # But for standard OpenAI, we might need to calculate it or it might be in extra data
            cost = 0.0
            if hasattr(response, 'cost'):
                cost = response.cost
            
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

            return {
                'content': ai_response,
                'tokens_used': tokens_used,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'response_time': response_time,
                'cost': cost,
                'model': assistant.get_model_name(),
            }

        except Exception as e:
            _logger.error(f"OpenAI API error: {e}")
            return {
                'content': _('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.'),
                'tokens_used': 0,
                'tokens_input': 0,
                'tokens_output': 0,
                'response_time': time.time() - start_time,
                'cost': 0.0,
                'model': assistant.get_model_name() if assistant else '',
            }
    
    def _build_messages(self, user_message, context):
        """Build message array for OpenAI"""
        messages = []
        
        # System prompt with security rules
        system_prompt = self._build_system_prompt(context)
        messages.append({
            'role': 'system',
            'content': system_prompt
        })
        
        # Conversation history
        history = context.get('messages', [])
        for msg in history[-5:]:  # Last 5 messages
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