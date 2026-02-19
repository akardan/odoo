# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
import threading
import re

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    is_ai_channel = fields.Boolean('AI Assistant Channel', default=False)
    ai_conversation_id = fields.Many2one('ak_ai.conversation', 'AI Conversation')

    @api.model
    def ensure_ai_channel(self):
        """Ensure KAI Assistant channel exists. Safe to call multiple times."""
        existing = self.search([('is_ai_channel', '=', True)], limit=1)
        if existing:
            # Ensure auto-subscription group is set
            group_user = self.env.ref('base.group_user')
            if group_user not in existing.group_ids:
                existing.group_ids = [(4, group_user.id)]
            # Ensure conversation is linked
            if not existing.ai_conversation_id:
                conversation = self.env['ak_ai.conversation'].create({
                    'integration_type': 'discuss',
                    'discuss_channel_id': existing.id,
                })
                existing.ai_conversation_id = conversation.id
            return existing
        return self.create_ai_channel()

    @api.model
    def create_ai_channel(self, name="KAI Assistant"):
        """Create AI assistant channel"""
        channel = self.create({
            'name': name,
            'channel_type': 'channel',
            'is_ai_channel': True,
            'group_ids': [(4, self.env.ref('base.group_user').id)],
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
            if message.author_id == self.env.user.partner_id:
                clean_body = re.sub(r'<[^>]+>', '', message.body or '').strip()
                if clean_body:
                    # Schedule AI processing AFTER current transaction commits
                    db_name = self.env.cr.dbname
                    uid = self.env.uid
                    channel_id = self.id
                    conversation_id = self.ai_conversation_id.id

                    def _after_commit():
                        _logger.info("KAI postcommit fired, starting AI thread for channel %s", channel_id)
                        thread = threading.Thread(
                            target=self._process_ai_in_thread,
                            args=(db_name, uid, channel_id, conversation_id, clean_body),
                            daemon=True,
                        )
                        thread.start()

                    self.env.cr.postcommit.add(_after_commit)
                    _logger.info("KAI postcommit registered for channel %s, text: %s", channel_id, clean_body[:50])

        return res

    @staticmethod
    def _process_ai_in_thread(db_name, uid, channel_id, conversation_id, user_text):
        """Process AI response in a background thread with its own cursor."""
        from odoo.modules.registry import Registry
        from odoo import api as odoo_api

        _logger.info("KAI AI thread started for channel %s", channel_id)
        reg = Registry(db_name)
        with reg.cursor() as cr:
            try:
                env = odoo_api.Environment(cr, uid, {})
                channel = env['discuss.channel'].browse(channel_id)
                conversation = env['ak_ai.conversation'].browse(conversation_id)

                # Ensure conversation user matches
                if conversation.user_id.id != uid:
                    conversation.sudo().write({'user_id': uid})
                    cr.commit()

                # Generate AI response
                _logger.info("KAI generating AI response for conversation %s", conversation_id)
                ai_message = conversation.add_message(user_text, 'user')
                _logger.info("KAI AI response received: %s chars, type=%s",
                             len(ai_message.content) if ai_message and ai_message.content else 0,
                             type(ai_message).__name__)

                # Commit AI message first so it's persisted
                cr.commit()

                # Re-browse after commit
                env = odoo_api.Environment(cr, uid, {})
                channel = env['discuss.channel'].browse(channel_id)

                # Post response back to Discuss channel
                if ai_message and ai_message.content:
                    ai_content = ai_message.content
                    # Re-browse ai_message in fresh env
                    ai_msg = env['ak_ai.message'].browse(ai_message.id)
                    channel.message_post(
                        body=ai_msg.content,
                        author_id=env.ref('base.partner_root').id,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
                    _logger.info("KAI response posted to Discuss channel %s", channel_id)
                    cr.commit()
                else:
                    _logger.warning("KAI: No AI response content to post")
            except Exception as e:
                _logger.error("Error in AI thread: %s", e, exc_info=True)
                cr.rollback()
                try:
                    env = odoo_api.Environment(cr, uid, {})
                    channel = env['discuss.channel'].browse(channel_id)
                    channel.message_post(
                        body="Sorry, I encountered an error: %s" % str(e),
                        author_id=env.ref('base.partner_root').id,
                        message_type='comment',
                    )
                    cr.commit()
                except Exception:
                    _logger.error("Failed to post error message", exc_info=True)
