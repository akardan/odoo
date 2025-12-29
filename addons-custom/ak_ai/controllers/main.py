# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class AkAiController(http.Controller):

    @http.route('/ak_ai/execute_code/<int:conversation_id>', type='http', auth='user')
    def execute_code(self, conversation_id, **kwargs):
        """Route to execute the last code block in a conversation"""
        conversation = request.env['ak_ai.conversation'].browse(conversation_id)
        if not conversation.exists() or conversation.user_id != request.env.user:
            return request.render('website.404')
            
        try:
            result = conversation.action_execute_last_code()
            
            # Redirect back to the record if possible
            if conversation.context_model and conversation.context_res_id:
                url = f"/web#id={conversation.context_res_id}&model={conversation.context_model}&view_type=form"
                return request.redirect(url)
            
            return request.render('ak_ai.execution_result', {
                'result': result,
                'conversation': conversation
            })
        except Exception as e:
            _logger.error(f"Error in execute_code route: {e}")
            return request.render('ak_ai.execution_error', {
                'error': str(e),
                'conversation': conversation
            })
