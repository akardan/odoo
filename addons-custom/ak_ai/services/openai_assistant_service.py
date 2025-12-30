# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError
import logging
import json
import requests
import time

_logger = logging.getLogger(__name__)

class AkAiServiceOpenAIAssistant(models.AbstractModel):
    """OpenAI Assistants API Service (Stateful)"""
    _name = 'ak_ai.service.openai_assistant'
    _inherit = 'ak_ai.service'
    _description = 'OpenAI Assistants API Service'

    def generate_response(self, user_message, context):
        """Generate response using OpenAI Assistants API"""
        assistant_config = self.env['ak_ai.assistant'].get_active_assistant()
        
        if not assistant_config.api_key:
            raise ValidationError(_('OpenAI API key is not configured'))
            
        if not assistant_config.ai_assistant_id:
            raise ValidationError(_('OpenAI Assistant ID is not configured'))

        # Get or create thread
        conversation_id = context.get('conversation', {}).get('id')
        conversation = self.env['ak_ai.conversation'].browse(conversation_id)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {assistant_config.api_key}",
            "OpenAI-Beta": "assistants=v2"
        }
        
        # 1. Create Thread if not exists
        if not conversation.thread_id:
            try:
                url = "https://api.openai.com/v1/threads"
                response = requests.post(url, headers=headers, json={})
                if response.status_code != 200:
                    raise Exception(f"Failed to create thread: {response.text}")
                
                thread_data = response.json()
                conversation.write({'thread_id': thread_data['id']})
                _logger.info(f"Created new OpenAI thread: {thread_data['id']}")
            except Exception as e:
                _logger.error(f"Error creating thread: {e}")
                raise ValidationError(_('Failed to initialize conversation thread'))

        thread_id = conversation.thread_id

        # 2. Add Message to Thread
        try:
            url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
            data = {
                "role": "user",
                "content": user_message
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                raise Exception(f"Failed to add message: {response.text}")
        except Exception as e:
            _logger.error(f"Error adding message to thread: {e}")
            raise ValidationError(_('Failed to send message to AI'))

        # 3. Run Assistant
        try:
            # Prepare context instructions
            user_context = context.get('user', {})
            record_context = context.get('record', {})
            
            additional_instructions = f"""
Current User: {user_context.get('name', 'Unknown')}
Current Context: {record_context.get('model', 'No Model')} (ID: {record_context.get('id', 0)})
Record Name: {record_context.get('display_name', '')}
"""
            
            url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
            data = {
                "assistant_id": assistant_config.ai_assistant_id,
                "additional_instructions": additional_instructions
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                raise Exception(f"Failed to start run: {response.text}")
            
            run_data = response.json()
            run_id = run_data['id']
        except Exception as e:
            _logger.error(f"Error starting run: {e}")
            raise ValidationError(_('Failed to start AI processing'))

        # 4. Poll for Completion
        # Wait for run to complete (simple polling for now)
        max_retries = 60  # 60 seconds timeout
        retry_count = 0
        
        while retry_count < max_retries:
            time.sleep(1)
            try:
                url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    continue
                
                run_status = response.json()
                status = run_status['status']
                
                if status == 'completed':
                    break
                elif status in ['failed', 'cancelled', 'expired']:
                    raise Exception(f"Run failed with status: {status}")
                elif status == 'requires_action':
                    # Handle function calling
                    self._handle_required_actions(run_status, thread_id, run_id, headers, conversation)
                    # Reset retry count to wait for new status after submitting outputs
                    retry_count = 0
                
                retry_count += 1
            except Exception as e:
                _logger.error(f"Error polling run: {e}")
                raise ValidationError(_('Error waiting for AI response'))

        if retry_count >= max_retries:
            raise ValidationError(_('AI response timed out'))

        # 5. Get Messages
        try:
            url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to get messages: {response.text}")
            
            messages_data = response.json()
            # Get the latest message from assistant
            latest_message = None
            for msg in messages_data['data']:
                if msg['role'] == 'assistant' and msg['run_id'] == run_id:
                    latest_message = msg
                    break
            
            if not latest_message:
                return "No response from assistant."
                
            # Extract text content
            content_parts = []
            for content in latest_message['content']:
                if content['type'] == 'text':
                    content_parts.append(content['text']['value'])
            
            return "\n".join(content_parts)

        except Exception as e:
            _logger.error(f"Error retrieving response: {e}")
            raise ValidationError(_('Failed to retrieve AI response'))

    def _handle_required_actions(self, run_status, thread_id, run_id, headers, conversation):
        """Handle tool calls from OpenAI Assistant"""
        required_action = run_status.get('required_action', {})
        submit_tool_outputs = required_action.get('submit_tool_outputs', {})
        tool_calls = submit_tool_outputs.get('tool_calls', [])
        
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            arguments = json.loads(tool_call['function']['arguments'])
            tool_call_id = tool_call['id']
            
            output = self._execute_tool(function_name, arguments, conversation)
            
            tool_outputs.append({
                "tool_call_id": tool_call_id,
                "output": str(output)
            })
            
        # Submit outputs back to OpenAI
        if tool_outputs:
            url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/submit_tool_outputs"
            response = requests.post(url, headers=headers, json={"tool_outputs": tool_outputs})
            if response.status_code != 200:
                raise Exception(f"Failed to submit tool outputs: {response.text}")

    def _execute_tool(self, function_name, arguments, conversation):
        """Execute the requested tool/function"""
        _logger.info(f"Executing tool: {function_name} with args: {arguments}")
        
        if function_name == 'execute_python_code':
            code = arguments.get('code')
            if code:
                result = conversation.execute_python_code(code)
                return json.dumps(result, default=str)
        
        return json.dumps({"error": f"Unknown function: {function_name}"})
