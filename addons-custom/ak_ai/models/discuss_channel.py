# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    is_ai_channel = fields.Boolean('AI Assistant Channel', default=False)
    ai_conversation_id = fields.Many2one('ak_ai.conversation', 'AI Conversation')
    
    @api.model
    def create_ai_channel(self, name="KAI Assistant"):
        """Create AI assistant channel"""
        channel = self.create({
            'name': name,
            'channel_type': 'channel',
            'is_ai_channel': True,
        })
        
        # Create conversation
        conversation = self.env['ak_ai.conversation'].create({
            'integration_type': 'discuss',
            'discuss_channel_id': channel.id,
        })
        
        channel.ai_conversation_id = conversation.id
        return channel
    
    def _message_post_after_hook(self, message, msg_vals):
        """Hook to process AI messages"""
        res = super()._message_post_after_hook(message, msg_vals)
        
        if self.is_ai_channel and self.ai_conversation_id:
            # Process user message for AI response
            if message.author_id == self.env.user.partner_id:
                self._process_ai_message(message)
                
        return res
    
    def _process_ai_message(self, message):
        """Process message for AI response"""
        try:
            # Send to AI conversation
            self.ai_conversation_id.send_message(message.body, 'user')
        except Exception as e:
            _logger.error(f"Error processing AI message: {e}")
            
            # Send error message
            self.message_post(
                body=_("Sorry, I encountered an error. Please try again."),
                author_id=self.env.ref('base.partner_root').id,
                message_type='comment'
            )