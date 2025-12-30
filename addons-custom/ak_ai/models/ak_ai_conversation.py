# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class AkAiConversation(models.Model):
    _name = 'ak_ai.conversation'
    _description = 'AI Conversation'
    _order = 'create_date desc'
    _rec_name = 'title'

    title = fields.Char('Title', compute='_compute_title', store=True)
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.user)
    
    # Context Information
    context_model = fields.Char('Context Model')  # e.g., 'sale.order'
    context_res_id = fields.Integer('Context Record ID')
    context_data = fields.Text('Context Data (JSON)')
    
    # Integration Type
    integration_type = fields.Selection([
        ('discuss', 'Discuss Channel'),
        ('chatter', 'Chatter Integration'),
        ('standalone', 'Standalone Chat'),
    ], string='Integration Type', default='discuss')
    
    # Discuss Integration
    discuss_channel_id = fields.Many2one('discuss.channel', 'Discuss Channel')
    
    # Assistants API Specifics
    thread_id = fields.Char('Thread ID', help="OpenAI Thread ID for stateful conversations")
    
    # Messages
    message_ids = fields.One2many('ak_ai.message', 'conversation_id', 'Messages')
    message_count = fields.Integer('Message Count', compute='_compute_message_count')
    
    # Temporary field for sending messages from form view
    new_message_content = fields.Text('New Message', store=False)
    
    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('error', 'Error'),
    ], string='State', default='active')
    
    last_message_date = fields.Datetime('Last Message', compute='_compute_last_message_date', store=True)
    
    @api.depends('message_ids')
    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.message_ids)
    
    @api.depends('message_ids.create_date')
    def _compute_last_message_date(self):
        for record in self:
            if record.message_ids:
                record.last_message_date = max(record.message_ids.mapped('create_date'))
            else:
                record.last_message_date = record.create_date
    
    @api.depends('message_ids')
    def _compute_title(self):
        for record in self:
            if record.message_ids:
                first_user_message = record.message_ids.filtered(lambda m: m.message_type == 'user')
                if first_user_message:
                    # Take first 50 chars of first user message
                    content = first_user_message[0].content
                    record.title = content[:50] + '...' if len(content) > 50 else content
                else:
                    record.title = _('New Conversation')
            else:
                record.title = _('New Conversation')
    
    def get_context_data(self):
        """Get context data for AI - only what user can access"""
        if not self.context_model or not self.context_res_id:
            return {}
            
        try:
            # Use user's environment (no sudo!)
            model = self.env[self.context_model]
            record = model.browse(self.context_res_id)
            
            # Check if user can read this record
            if not record.exists():
                return {}
                
            # This will automatically apply record rules and field access
            context_data = self._extract_record_context(record)
            return context_data
            
        except AccessError:
            _logger.warning(f"User {self.env.user.name} cannot access {self.context_model}({self.context_res_id})")
            return {}
        except Exception as e:
            _logger.error(f"Error getting context data: {e}")
            return {}
    
    def _extract_record_context(self, record):
        """Extract context from record - respects field access"""
        context = {
            'model': record._name,
            'id': record.id,
            'display_name': record.display_name,
        }
        
        # Get readable fields only
        try:
            field_data = {}
            for field_name, field in record._fields.items():
                # Skip technical and binary fields
                if field_name.startswith('_') or field.type == 'binary':
                    continue
                if field_name in ['create_uid', 'write_uid', 'create_date', 'write_date']:
                    continue
                    
                try:
                    value = record[field_name]
                    
                    if field.type in ('char', 'text', 'html', 'selection'):
                        if value:
                            field_data[field_name] = value
                    elif field.type in ('integer', 'float', 'monetary'):
                        field_data[field_name] = value
                    elif field.type == 'boolean':
                        field_data[field_name] = value
                    elif field.type in ('date', 'datetime'):
                        try:
                            field_data[field_name] = value.isoformat() if value else None
                        except Exception:
                            continue
                    elif field.type == 'many2one':
                        try:
                            field_data[field_name] = {
                                'id': value.id,
                                'name': value.display_name
                            } if value else None
                        except Exception:
                            continue
                    elif field.type in ('one2many', 'many2many'):
                        # Include detailed data for first few records
                        lines_data = []
                        # Limit to first 50 records to avoid huge context
                        for line in value[:50]:
                            try:
                                line_info = {'id': line.id, 'display_name': line.display_name}
                                # Extract basic fields from related record
                                for lf_name, lf in line._fields.items():
                                    if lf_name.startswith('_') or lf.type in ('binary', 'reference'):
                                        continue
                                    if lf_name in ['id', 'display_name', 'create_uid', 'write_uid', 'create_date', 'write_date']:
                                        continue
                                    try:
                                        lv = line[lf_name]
                                        if lv is False and lf.type != 'boolean':
                                            continue
                                        
                                        # Handle nested x2many - provide summary only
                                        if lf.type in ('one2many', 'many2many'):
                                            line_info[lf_name] = {
                                                'count': len(lv),
                                                'model': getattr(lv, '_name', 'unknown')
                                            }
                                            continue

                                        if lf.type in ('char', 'text', 'html', 'selection'):
                                            line_info[lf_name] = lv
                                        elif lf.type in ('integer', 'float', 'monetary'):
                                            line_info[lf_name] = lv
                                        elif lf.type == 'boolean':
                                            line_info[lf_name] = lv
                                        elif lf.type in ('date', 'datetime'):
                                            line_info[lf_name] = lv.isoformat() if lv else None
                                        elif lf.type == 'many2one':
                                            line_info[lf_name] = {
                                                'id': lv.id, 
                                                'name': lv.display_name,
                                                'model': getattr(lv, '_name', 'unknown')
                                            } if lv else None
                                    except Exception:
                                        continue
                                lines_data.append(line_info)
                            except Exception:
                                continue
                        
                        field_data[field_name] = {
                            'count': len(value),
                            'items': lines_data,
                            'has_more': len(value) > 50
                        }
                except Exception as e:
                    # Log field-level errors but continue
                    _logger.debug(f"Error reading field {field_name} on {record._name}: {e}")
                    continue
                    
            context['fields'] = field_data
            
            # Add related data if user has access
            context['related'] = self._get_related_data(record)
            
        except Exception as e:
            error_msg = f"Error extracting record context: {str(e)}"
            _logger.error(error_msg)
            context['extraction_error'] = error_msg
            
        return context
    
    def _get_related_data(self, record):
        """Get related data user has access to"""
        related = {}
        
        try:
            # Common related data patterns
            if hasattr(record, 'order_line') and record.order_line:
                # Sales/Purchase order lines
                related['lines_count'] = len(record.order_line)
                
            if hasattr(record, 'invoice_ids') and record.invoice_ids:
                # Related invoices
                related['invoices_count'] = len(record.invoice_ids)
                
            if hasattr(record, 'picking_ids') and record.picking_ids:
                # Related deliveries
                related['deliveries_count'] = len(record.picking_ids)
                
            if hasattr(record, 'message_ids') and record.message_ids:
                # Chatter messages
                related['messages_count'] = len(record.message_ids)
                
        except AccessError:
            # User doesn't have access to related data
            pass
            
        return related
    
    @api.model
    def create_conversation(self, integration_type='discuss', context_model=None, context_res_id=None):
        """Create new conversation with user permissions"""
        
        # Check if user has access to context record
        if context_model and context_res_id:
            try:
                record = self.env[context_model].browse(context_res_id)
                if not record.exists():
                    raise ValidationError(_('Record not found or access denied'))
            except AccessError:
                raise ValidationError(_('You do not have access to this record'))
        
        conversation = self.create({
            'integration_type': integration_type,
            'context_model': context_model,
            'context_res_id': context_res_id,
            'user_id': self.env.user.id,
        })
        
        return conversation
    
    def send_message(self):
        """Send message from form view button"""
        self.ensure_one()
        
        # Check user access
        if self.user_id != self.env.user:
            raise AccessError(_('You can only send messages in your own conversations'))
        
        # Get the message content from context or field
        content = self._context.get('message_content') or self.new_message_content
        
        # Check if there's content
        if not content or not content.strip():
            raise ValidationError(_('Please enter a message'))
        
        # Create user message
        message = self.env['ak_ai.message'].create({
            'conversation_id': self.id,
            'content': content.strip(),
            'message_type': 'user',
            'user_id': self.env.user.id,
        })
        
        # Clear the input field
        self.write({'new_message_content': False})
        
        # Trigger AI response
        self._generate_ai_response(message)
        
        # Return reload action to refresh messages
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def add_message(self, content, message_type='user'):
        """Programmatic method to send message in conversation"""
        
        # Check user access
        if self.user_id != self.env.user:
            raise AccessError(_('You can only send messages in your own conversations'))
        
        message = self.env['ak_ai.message'].create({
            'conversation_id': self.id,
            'content': content,
            'message_type': message_type,
            'user_id': self.env.user.id,
        })
        
        # If user message, trigger AI response
        if message_type == 'user':
            self._generate_ai_response(message)
            
        return message
    
    def _generate_ai_response(self, user_message):
        """Generate AI response - uses AI service"""
        max_retries = 5
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                _logger.info(f"Generating AI response for conversation {self.id} (Attempt {retry_count + 1})")
                # Get AI service
                ai_service = self.env['ak_ai.service'].get_service()
                
                # Get context data
                context_data = self.get_context_data()
                
                # DEBUG: Log context data size
                import sys
                context_size = sys.getsizeof(str(context_data))
                _logger.info(f"Context data size: {context_size} bytes, fields count: {len(context_data.get('fields', {}))}")
                
                # Get conversation history
                history = self._get_conversation_history(limit=5)
                
                # Prepare context for AI
                context = {
                    'record': context_data,
                    'messages': history,
                    'history': history,
                    'user': {
                        'name': self.env.user.name,
                        'lang': self.env.user.lang,
                    },
                    'conversation': context_data,
                }
                
                # DEBUG: Log what fields are being sent
                if context_data and 'fields' in context_data:
                    _logger.info(f"Fields being sent to AI: {list(context_data['fields'].keys())}")
                    # Check if user_input_ids exists and has data
                    if 'user_input_ids' in context_data['fields']:
                        user_inputs = context_data['fields']['user_input_ids']
                        _logger.info(f"user_input_ids: count={user_inputs.get('count')}, items={len(user_inputs.get('items', []))}")
                
                # If this is a retry, add error info to prompt
                current_prompt = user_message.content
                if retry_count > 0 and last_error:
                    current_prompt = "Önceki kod çalıştırma hatası: " + str(last_error) + "\n\nLütfen kodu düzeltip tekrar dene.\n\nKullanıcı isteği: " + str(user_message.content)

                # Generate response using AI service
                response_content = ai_service.generate_response(
                    user_message=current_prompt,
                    context=context
                )
                
                # Check for credit error in response
                if "Insufficient credits" in response_content or "402" in response_content:
                    response_content = "🤖 **KAI Notu:** OpenRouter kredisi tükenmiş görünüyor. Lütfen sistem yöneticisine haber verin."
                    break # Don't retry credit errors
                
                # Check if response contains code to execute
                import re
                code_match = re.search(r'\[EXECUTE_CODE\](.*?)\[/EXECUTE_CODE\]', response_content, re.DOTALL)
                
                if code_match:
                    code = code_match.group(1).strip()
                    _logger.info(f"Auto-executing code attempt {retry_count + 1}")
                    
                    # Execute code
                    exec_result = self.execute_python_code(code)
                    
                    if exec_result.get('success'):
                        # Code executed successfully!
                        # Append the code and result to the response content
                        result_message = exec_result.get('message', '')
                        result_details = exec_result.get('result', '')
                        response_content += f"\n\n**Çalıştırılan Kod:**\n```python\n{code}\n```\n\n**Sonuç:** {result_message}"
                        if result_details:
                            response_content += f"\n\n**Detaylar:** ```\n{result_details}\n```"
                        break
                    else:
                        # Code failed, retry with error info
                        last_error = exec_result.get('error')
                        _logger.warning("Code execution failed: " + str(last_error))
                        retry_count += 1
                        continue
                else:
                    # No code to execute, just return the response
                    break
                    
            except Exception as e:
                _logger.error(f"Error generating AI response: {e}", exc_info=True)
                last_error = str(e)
                retry_count += 1
                if retry_count >= max_retries:
                    break

        # Final response handling
        if last_error and retry_count >= max_retries:
            if "402" in str(last_error) or "Insufficient credits" in str(last_error):
                msg = "🤖 **KAI Notu:** OpenRouter kredisi tükenmiş görünüyor. Lütfen sistem yöneticisine haber verin."
            else:
                msg = 'Üzgünüm, 5 denemeden sonra hala hata alıyorum. Lütfen tekrar deneyin.\n\nSon hata detayı: ' + str(last_error)
            response_content = msg

        # Create AI message
        ai_message = self.env['ak_ai.message'].create({
            'conversation_id': self.id,
            'content': response_content,
            'message_type': 'assistant',
            'user_id': self.env.user.id,
        })
        
        return ai_message
    
    def _get_conversation_history(self, limit=5):
        """Get conversation history for context - optimized to reduce token usage"""
        # Reduced from 10 to 5 to save tokens
        messages = self.message_ids.sorted('create_date')[-limit:]
        
        history = []
        for message in messages:
            # Truncate very long assistant messages to save tokens
            content = message.content
            if message.message_type == 'assistant' and len(content) > 2000:
                # Keep first "2000" chars for context
                content = content[:2000] + "\n...(truncated for context)..."
            
            history.append({
                'role': 'user' if message.message_type == 'user' else 'assistant',
                'content': content,
                'timestamp': message.create_date.isoformat(),
            })
            
        return history

    def action_execute_last_code(self):
        """Execute the last code block found in the conversation"""
        self.ensure_one()
        last_assistant_message = self.message_ids.filtered(lambda m: m.message_type == 'assistant').sorted('create_date', reverse=True)[:1]
        if not last_assistant_message:
            raise ValidationError(_('No code block found in the last assistant message'))
            
        import re
        code_match = re.search(r'\[EXECUTE_CODE\](.*?)\[/EXECUTE_CODE\]', last_assistant_message.content, re.DOTALL)
        if not code_match:
            raise ValidationError(_('No [EXECUTE_CODE] block found in the last message'))
            
        code = code_match.group(1).strip()
        return self.execute_python_code(code)

    def execute_python_code(self, code):
        """Execute Python code safely with user permissions"""
        self.ensure_one()
        
        # Check user access
        if self.user_id != self.env.user:
            raise AccessError(_('You can only execute code in your own conversations'))
            
        try:
            # Prepare restricted execution environment
            from datetime import datetime, timedelta
            exec_env = {
                'env': self.env,
                'user': self.env.user,
                'company': self.env.company,
                'datetime': datetime,
                'timedelta': timedelta,
                'json': json,
                'fields': fields,
                'models': models,
                '_': _,
                'log': _logger.info,
                'result': None,
            }
            
            # Add context record if available
            if self.context_model and self.context_res_id:
                record = self.env[self.context_model].browse(self.context_res_id)
                if record.exists():
                    exec_env['record'] = record
                    exec_env['records'] = record
            
            # Execute code
            # Note: We don't use sudo() here, so it respects user permissions
            exec(code, exec_env)
            
            result = exec_env.get('result')
            
            # Log execution
            assistant = self.env['ak_ai.assistant'].get_active_assistant()
            self.env['ak_ai.interaction_log'].create({
                'user_id': self.env.user.id,
                'user_message': 'EXECUTE CODE:\n' + str(code),
                'ai_response': 'RESULT: ' + str(result),
                'ai_provider': assistant.ai_provider,
            })
            
            return {
                'success': True,
                'result': result,
                'message': 'İşlem başarıyla tamamlandı'
            }
            
        except Exception as e:
            _logger.error(f"Error executing AI code: {e}")
            error_message = f"Kod çalıştırma hatası: {str(e)}"
            return {
                'success': False,
                'error': str(e),
                'message': error_message
            }
