# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class AkAiMixin(models.AbstractModel):
    """Mixin to add AI capabilities to any model"""
    _name = 'ak_ai.mixin'
    _description = 'AI Assistant Mixin'

    # AI Integration Fields
    ai_conversation_id = fields.Many2one('ak_ai.conversation', 'AI Conversation', copy=False)
    ai_enabled = fields.Boolean('AI Enabled', default=True)
    
    def get_or_create_ai_conversation(self):
        """Get existing conversation or create a new one for this record"""
        self.ensure_one()
        
        if not self.ai_conversation_id:
            # Create new conversation
            conversation = self.env['ak_ai.conversation'].create({
                'title': f'{self._description or self._name} - {self.display_name}',
                'user_id': self.env.user.id,
                'integration_type': 'chatter',
                'context_model': self._name,
                'context_res_id': self.id,
            })
            self.ai_conversation_id = conversation.id
        
        return {
            'conversation_id': self.ai_conversation_id.id,
        }
    
    def open_ai_chat(self):
        """Open AI chat for this record"""
        self.ensure_one()
        
        # Check if conversation exists
        if not self.ai_conversation_id:
            # Create new conversation
            conversation = self.env['ak_ai.conversation'].create_conversation(
                integration_type='chatter',
                context_model=self._name,
                context_res_id=self.id
            )
            self.ai_conversation_id = conversation.id
        
        # Return action to open chat
        return {
            'type': 'ir.actions.act_window',
            'name': _('AI Assistant'),
            'res_model': 'ak_ai.conversation',
            'res_id': self.ai_conversation_id.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def ask_ai(self, question):
        """Ask AI a question about this record"""
        self.ensure_one()
        
        if not self.ai_conversation_id:
            conversation = self.env['ak_ai.conversation'].create_conversation(
                integration_type='chatter',
                context_model=self._name,
                context_res_id=self.id
            )
            self.ai_conversation_id = conversation.id
        
        # Send message and get response
        message = self.ai_conversation_id.send_message(question, 'user')
        return message
    
    def send_ai_message(self, message_content):
        """Send message to KAI and post response to chatter"""
        self.ensure_one()
        
        # Get or create conversation
        if not self.ai_conversation_id:
            conversation_info = self.get_or_create_ai_conversation()
        
        try:
            # Post user's question to chatter first
            user_question_html = Markup(f"""<div style="border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; background-color: #f1f9f3;">
<p style="margin: 0 0 5px 0;"><strong style="color: #28a745;">💬 Soru</strong></p>
<div style="color: #333;">{message_content}</div>
</div>""")
            
            self.message_post(
                body=user_question_html,
                subject=_("Question to KAI"),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
            
            # Send message to AI
            user_message = self.env['ak_ai.message'].create({
                'conversation_id': self.ai_conversation_id.id,
                'content': message_content,
                'message_type': 'user',
                'user_id': self.env.user.id,
            })
            
            # Get AI response
            ai_response = self.ai_conversation_id._generate_ai_response(user_message)
            
            # Format response as HTML (Simple Markdown to HTML conversion)
            content = ai_response.content
            
            # Handle [EXECUTE_CODE] blocks
            import re
            def format_code_block(match):
                code = match.group(1).strip()
                # Escape HTML in code
                import html
                escaped_code = html.escape(code)
                return f"""<div style="margin: 15px 0; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="background-color: #f8f9fa; padding: 8px 15px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; color: #444; font-size: 0.9em;">🐍 Python Kodu</span>
                        <span style="background-color: #e9ecef; color: #495057; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">Onay Bekliyor</span>
                    </div>
                    <pre style="margin: 0; padding: 15px; background-color: #272822; color: #f8f8f2; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace; font-size: 0.9em; overflow-x: auto; line-height: 1.4;">{escaped_code}</pre>
                    <div style="padding: 10px 15px; background-color: #fff; border-top: 1px solid #e0e0e0; text-align: right;">
                        <p style="margin: 0 0 10px 0; font-size: 0.85em; color: #666; text-align: left;">⚠️ Bu kod sizin yetkilerinizle çalıştırılacaktır.</p>
                        <a href="/ak_ai/execute_code/{self.ai_conversation_id.id}"
                           style="display: inline-block; padding: 10px 20px; background-color: #0066cc; color: #ffffff !important; text-decoration: none !important; border-radius: 4px; font-weight: bold; font-size: 1em; border: none;">Kodu Çalıştır</a>
                    </div>
                </div>"""
            
            content = re.sub(r'\[EXECUTE_CODE\](.*?)\[/EXECUTE_CODE\]', format_code_block, content, flags=re.DOTALL)
            
            # Convert headers
            content = re.sub(r'^### (.*)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
            content = re.sub(r'^## (.*)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
            content = re.sub(r'^# (.*)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
            
            # Convert bold
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            
            # Convert lists
            content = re.sub(r'^\- (.*)$', r'<li>\1</li>', content, flags=re.MULTILINE)
            content = re.sub(r'^\d+\. (.*)$', r'<li>\1</li>', content, flags=re.MULTILINE)
            
            # Wrap lists in <ul> (very basic)
            if '<li>' in content:
                content = content.replace('<li>', '<ul><li>', 1)
            
            # Convert newlines to <br/> (but not inside our custom div)
            # This is tricky, let's just do it for now
            response_html = content.replace('\n', '<br/>')
            
            # Create safe HTML using Markup
            safe_html = Markup(f"""<div style="border-left: 4px solid #0066cc; padding: 15px; margin: 10px 0; background-color: #f8f9fa; border-radius: 0 5px 5px 0; font-family: sans-serif;">
<p style="margin: 0 0 10px 0;"><strong style="color: #0066cc; font-size: 1.1em;">✨ KAI - AI Asistan</strong></p>
<div style="color: #333; line-height: 1.5;">{response_html}</div>
</div>""")
            
            # Post KAI response to chatter
            self.message_post(
                body=safe_html,
                subject=_("KAI Response"),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
            
            return {
                'success': True,
                'message': 'Message sent successfully',
                'response': ai_response.content,
            }
            
        except Exception as e:
            _logger.error(f"Error sending AI message: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def action_execute_ai_code(self):
        """Execute the last code block from the associated conversation"""
        self.ensure_one()
        if not self.ai_conversation_id:
            raise ValidationError(_('No AI conversation found for this record'))
        return self.ai_conversation_id.action_execute_last_code()

    def get_ai_suggestions(self):
        """Get AI suggestions for this record"""
        self.ensure_one()
        
        # Build context-aware question
        model_name = self._description or self._name
        question = f"Bu {model_name} kaydı için önerileriniz nelerdir?"
        
        return self.ask_ai(question)