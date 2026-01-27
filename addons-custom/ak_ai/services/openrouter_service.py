# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError
import logging
import time
import json
import requests

_logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    openai = None


class AkAiServiceOpenRouter(models.Model):
    _name = 'ak_ai.service.openrouter'
    _inherit = 'ak_ai.service'
    _description = 'OpenRouter Service'

    @api.model
    def get_available_models(self, provider=None):
        """Get available models from OpenRouter API"""
        models = []
        
        try:
            # Try to fetch from OpenRouter API
            assistant = self.env['ak_ai.assistant'].search([('ai_provider', '=', 'openrouter')], limit=1)
            
            headers = {}
            if assistant and assistant.api_key:
                headers['Authorization'] = f'Bearer {assistant.api_key}'
            
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                for model in data.get('data', []):
                    model_id = model.get('id')
                    model_name = model.get('name', model_id)
                    context_length = model.get('context_length', 0)
                    
                    # Create display name with context length
                    display_name = f"{model_name}"
                    if context_length:
                        display_name += f" ({context_length//1000}k)"
                    
                    if model_id:
                        models.append((model_id, display_name))
                
                # Sort by popularity/name and limit
                models = models[:100]  # Limit to 100 most popular
                
        except Exception as e:
            _logger.warning(f"Could not fetch OpenRouter models from API: {e}")
        
        # Fallback to common models if API call failed
        if not models:
            models = [
                ('anthropic/claude-opus-4', 'Claude Opus 4'),
                ('anthropic/claude-sonnet-4', 'Claude Sonnet 4'),
                ('anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet'),
                ('anthropic/claude-3.5-haiku', 'Claude 3.5 Haiku'),
                ('openai/gpt-4o', 'GPT-4o'),
                ('openai/gpt-4o-mini', 'GPT-4o Mini'),
                ('openai/gpt-4-turbo', 'GPT-4 Turbo'),
                ('google/gemini-pro-1.5', 'Gemini Pro 1.5'),
                ('google/gemini-flash-1.5', 'Gemini Flash 1.5'),
                ('meta-llama/llama-3.3-70b-instruct', 'Llama 3.3 70B'),
                ('meta-llama/llama-3.1-405b-instruct', 'Llama 3.1 405B'),
                ('qwen/qwen-2.5-72b-instruct', 'Qwen 2.5 72B'),
                ('mistralai/mistral-large', 'Mistral Large'),
                ('deepseek/deepseek-chat', 'DeepSeek Chat'),
            ]
        
        # Always add custom option
        models.append(('custom', 'Custom Model (Enter Below)'))
        
        return models

    def generate_response(self, user_message, context):
        """Generate response using OpenRouter (OpenAI-compatible API)"""
        if not openai:
            raise ValidationError(_('OpenAI library not installed. Run: pip install openai'))
        
        assistant = self.env['ak_ai.assistant'].get_active_assistant()
        
        if not assistant.api_key:
            raise ValidationError(_('OpenRouter API key not configured'))
        
        start_time = time.time()
        
        try:
            # Configure OpenRouter with OpenAI client
            # OpenRouter uses OpenAI-compatible API
            client = openai.OpenAI(
                api_key=assistant.api_key,
                base_url=assistant.api_base_url or 'https://openrouter.ai/api/v1'
            )
            
            # Build messages
            messages = self._build_messages(user_message, context)
            
            # Get site URL and app name for OpenRouter headers
            site_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'https://localhost')
            app_name = self.env['ir.config_parameter'].sudo().get_param('ak_ai.app_name', 'Odoo AI Assistant')
            
            # Call OpenRouter API with custom headers
            response = client.chat.completions.create(
                model=assistant.get_model_name(),
                messages=messages,
                max_tokens=assistant.max_tokens,
                temperature=assistant.temperature,
                extra_headers={
                    "HTTP-Referer": site_url,  # Optional: site URL for rankings
                    "X-Title": app_name,  # Optional: app name for rankings
                }
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract token usage and cost
            tokens_input = response.usage.prompt_tokens if response.usage else 0
            tokens_output = response.usage.completion_tokens if response.usage else 0
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # OpenRouter often provides cost in the response
            cost = 0.0
            if hasattr(response, 'cost'):
                cost = response.cost
            elif response.usage and hasattr(response.usage, 'cost'):
                cost = response.usage.cost
            
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
            _logger.error(f"OpenRouter API error: {e}", exc_info=True)
            # Return the error message directly so it can be seen in the UI
            return f"🤖 **KAI Notu:** Bir hata oluştu.\n\nHata detayı: {str(e)}"
    
    def _build_messages(self, user_message, context):
        """Build message array for OpenRouter (OpenAI-compatible format)"""
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
