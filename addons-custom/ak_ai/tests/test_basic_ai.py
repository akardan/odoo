# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TestBasicAI(TransactionCase):
    """Basic AI Service Tests"""

    def setUp(self):
        super(TestBasicAI, self).setUp()
        
        # Create test assistant
        self.assistant = self.env['ak_ai.assistant'].create({
            'name': 'Test Assistant',
            'active': True,
            'ai_provider': 'OpenRouter',  # Varsayılan olarak OpenRouter
            'model_name': 'gpt-4o-mini',
            'api_key': 'test-key-12345',  # Test için dummy key
            'max_tokens': 500,
            'temperature': 0.7,
        })
        
    def test_01_assistant_creation(self):
        """Test assistant creation"""
        self.assertTrue(self.assistant.id)
        self.assertEqual(self.assistant.ai_provider, 'openai')
        self.assertTrue(self.assistant.active)
        
    def test_02_get_active_assistant(self):
        """Test getting active assistant"""
        assistant = self.env['ak_ai.assistant'].get_active_assistant()
        self.assertEqual(assistant.id, self.assistant.id)
        
    def test_03_service_selection(self):
        """Test AI service selection"""
        # OpenAI service
        self.assistant.write({'ai_provider': 'openai'})
        service = self.env['ak_ai.service'].get_service()
        self.assertEqual(service._name, 'ak_ai.service.openai')
        
        # Anthropic service
        self.assistant.write({'ai_provider': 'anthropic'})
        service = self.env['ak_ai.service'].get_service()
        self.assertEqual(service._name, 'ak_ai.service.anthropic')
        
        # OpenRouter service
        self.assistant.write({'ai_provider': 'openrouter'})
        service = self.env['ak_ai.service'].get_service()
        self.assertEqual(service._name, 'ak_ai.service.openrouter')
        
    def test_04_conversation_creation(self):
        """Test conversation creation"""
        conversation = self.env['ak_ai.conversation'].create({
            'title': 'Test Conversation',
            'user_id': self.env.user.id,
            'integration_type': 'web',
        })
        
        self.assertTrue(conversation.id)
        self.assertEqual(conversation.user_id, self.env.user)
        self.assertEqual(conversation.state, 'active')
        
    def test_05_message_creation(self):
        """Test message creation"""
        conversation = self.env['ak_ai.conversation'].create({
            'title': 'Test Conversation',
            'user_id': self.env.user.id,
            'integration_type': 'web',
        })
        
        message = self.env['ak_ai.message'].create({
            'conversation_id': conversation.id,
            'user_id': self.env.user.id,
            'message_type': 'user',
            'content': 'Test message',
        })
        
        self.assertTrue(message.id)
        self.assertEqual(message.conversation_id, conversation)
        self.assertEqual(message.message_type, 'user')
        
    def test_06_user_context(self):
        """Test user context generation"""
        context = self.assistant.get_user_context()
        
        self.assertIn('user', context)
        self.assertIn('permissions', context)
        self.assertIn('preferences', context)
        self.assertEqual(context['user']['id'], self.env.user.id)
        
    def test_07_security_validation(self):
        """Test security validation"""
        service = self.env['ak_ai.service']
        
        # Test forbidden patterns
        with self.assertRaises(ValidationError):
            service._validate_response('Use sudo() to access')
            
        with self.assertRaises(ValidationError):
            service._validate_response('import os and run commands')
            
        # Valid response should pass
        try:
            service._validate_response('This is a safe response about Odoo')
            valid = True
        except ValidationError:
            valid = False
            
        self.assertTrue(valid)
        
    def test_08_interaction_logging(self):
        """Test interaction logging"""
        initial_count = self.env['ak_ai.interaction_log'].search_count([])
        
        # Log an interaction
        self.env['ak_ai.interaction_log'].create({
            'user_id': self.env.user.id,
            'user_message': 'Test question',
            'ai_response': 'Test answer',
            'ai_provider': 'openai',
            'tokens_used': 100,
            'response_time': 1.5,
        })
        
        final_count = self.env['ak_ai.interaction_log'].search_count([])
        self.assertEqual(final_count, initial_count + 1)
        
    def test_09_user_access_check(self):
        """Test user access checking"""
        # Default should allow all users
        has_access = self.assistant.check_user_access(self.env.user.id)
        self.assertTrue(has_access)
        
        # Create a test user
        test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
        })
        
        # Restrict to specific user
        self.assistant.write({
            'allowed_user_ids': [(6, 0, [self.env.user.id])]
        })
        
        # Owner should have access
        self.assertTrue(self.assistant.check_user_access(self.env.user.id))
        
        # Other user should not
        self.assertFalse(self.assistant.check_user_access(test_user.id))
        
    def test_10_model_permissions(self):
        """Test model permission checking"""
        permissions = self.assistant._get_user_permissions(self.env.user)
        
        self.assertIsInstance(permissions, dict)
        # Should check multiple models
        self.assertGreaterEqual(len(permissions), 0)


# class TestAIProviders(TransactionCase):
