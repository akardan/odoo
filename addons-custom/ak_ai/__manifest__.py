# -*- coding: utf-8 -*-
{
    'name': 'KAI - Kardan AI Assistant',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Intelligent AI assistant for Odoo with context-aware help and task automation',
    'description': """
KAI (Kardan AI) Assistant
=========================

An intelligent AI assistant that provides:
- Context-aware help and guidance
- Task automation and suggestions
- Natural language interaction
- Learning from user feedback
- Secure user-permission-based operations

Features:
- Discuss channel integration for general assistance
- Chatter integration for context-aware help
- Dynamic tool system for extensible actions
- Comprehensive knowledge of Odoo structure
- User permission model (no sudo operations)
- Complete audit trail and security
    """,
    'author': 'Kardan.Digital',
    'website': 'https://kardan.digital',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'contacts',
        'sale',
        'purchase',
        'account',
    ],
    'external_dependencies': {
        'python': ['openai', 'anthropic', 'tiktoken'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/ak_ai_security.xml',
        'data/ak_ai_data.xml',
        'views/ak_ai_assistant_views.xml',
        'views/ak_ai_conversation_views.xml',
        'views/ak_ai_knowledge_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ak_ai/static/src/js/**/*',
            'ak_ai/static/src/xml/**/*',
            'ak_ai/static/src/css/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
}