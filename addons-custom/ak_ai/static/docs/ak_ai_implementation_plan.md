# AK_AI (KAI) - Complete Implementation Plan

## Project Overview

**Module Name**: `ak_ai`  
**Display Name**: KAI - Kardan AI Assistant  
**Version**: 1.0  
**License**: LGPL-3  
**Author**: Kardan.Digital

## Branding

- **Internal Code**: ak_ai
- **User-Facing Brand**: KAI (Kardan AI)
- **Bot Name**: KAI
- **Smart Button**: "Ask KAI"
- **Channel Name**: "🤖 KAI Assistant"
- **Icon**: Robot/AI themed

## Complete File Structure

```
addons-custom/ak_ai/
├── __init__.py
├── __manifest__.py
├── README.md
│
├── models/
│   ├── __init__.py
│   ├── ak_ai_assistant.py           # AI Configuration
│   ├── ak_ai_conversation.py        # Conversations
│   ├── ak_ai_message.py             # Messages
│   ├── ak_ai_prompt_template.py     # Prompt Templates
│   ├── ak_ai_usage_log.py           # Usage Tracking
│   ├── ak_ai_mixin.py               # Mixin for models
│   ├── discuss_channel.py           # Discuss integration
│   ├── res_partner.py               # Bot partner
│   ├── res_users.py                 # Bot user
│   └── ir_http.py                   # Session hooks
│
├── services/
│   ├── __init__.py
│   ├── base_ai_service.py           # Abstract base class
│   ├── openai_service.py            # OpenAI integration
│   ├── anthropic_service.py         # Anthropic integration
│   └── local_llm_service.py         # Local LLM support
│
├── controllers/
│   ├── __init__.py
│   ├── main.py                      # HTTP controllers
│   └── portal.py                    # Portal access
│
├── views/
│   ├── ak_ai_conversation_views.xml
│   ├── ak_ai_message_views.xml
│   ├── ak_ai_assistant_views.xml
│   ├── ak_ai_prompt_template_views.xml
│   ├── ak_ai_usage_log_views.xml
│   ├── res_config_settings_views.xml
│   ├── discuss_channel_views.xml
│   └── menu.xml
│
├── security/
│   ├── ir.model.access.csv
│   └── ak_ai_security.xml
│
├── data/
│   ├── ak_ai_data.xml               # Bot user/partner
│   ├── ak_ai_prompt_templates.xml   # Default templates
│   ├── ak_ai_cron.xml               # Scheduled actions
│   └── discuss_channel_data.xml     # Default channels
│
├── demo/
│   └── ak_ai_demo.xml
│
├── static/
│   ├── description/
│   │   ├── icon.png
│   │   ├── banner.png
│   │   └── index.html
│   │
│   └── src/
│       ├── js/
│       │   ├── kai_chat_widget.js       # Main chat widget
│       │   ├── kai_conversation.js      # Conversation component
│       │   ├── kai_message.js           # Message component
│       │   ├── kai_discuss_patch.js     # Discuss integration
│       │   └── kai_form_patch.js        # Form view integration
│       │
│       ├── xml/
│       │   ├── kai_chat_widget.xml      # Widget templates
│       │   ├── kai_conversation.xml     # Conversation templates
│       │   └── kai_message.xml          # Message templates
│       │
│       ├── css/
│       │   ├── kai_chat.css             # Chat styling
│       │   └── kai_widget.css           # Widget styling
│       │
│       └── img/
│           ├── kai_logo.png
│           └── kai_avatar.png
│
├── tests/
│   ├── __init__.py
│   ├── test_conversation.py
│   ├── test_ai_service.py
│   └── test_context.py
│
└── i18n/
    ├── tr_TR.po
    └── en_US.po
```

## Implementation Phases

### Phase 1: Foundation (Week 1)

#### 1.1 Module Structure
```bash
# Create directory structure
mkdir -p addons-custom/ak_ai/{models,services,controllers,views,security,data,demo,static/{description,src/{js,xml,css,img}},tests,i18n}
```

#### 1.2 Core Models

**File: [`__manifest__.py`](addons-custom/ak_ai/__manifest__.py)**
```python
{
    'name': 'KAI - Kardan AI Assistant',
    'version': '1.0.0',
    'category': 'Productivity',
    'summary': 'Intelligent AI Assistant for Odoo',
    'description': """
        KAI (Kardan AI) - Your Intelligent Odoo Assistant
        ==================================================
        
        Dual Integration:
        - Discuss Channel: General AI assistance
        - Chatter Integration: Context-aware help on records
        
        Features:
        - Natural language interaction
        - Context-aware assistance
        - Task automation
        - Data analysis
        - Multi-lingual support (TR/EN)
        - Multiple AI providers (OpenAI, Anthropic)
        
        Perfect for improving user productivity and Odoo adoption!
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
        # Security
        'security/ak_ai_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/ak_ai_data.xml',
        'data/ak_ai_prompt_templates.xml',
        'data/discuss_channel_data.xml',
        'data/ak_ai_cron.xml',
        
        # Views
        'views/ak_ai_assistant_views.xml',
        'views/ak_ai_conversation_views.xml',
        'views/ak_ai_message_views.xml',
        'views/ak_ai_prompt_template_views.xml',
        'views/ak_ai_usage_log_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/ak_ai_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ak_ai/static/src/css/kai_chat.css',
            'ak_ai/static/src/css/kai_widget.css',
            'ak_ai/static/src/js/kai_chat_widget.js',
            'ak_ai/static/src/js/kai_conversation.js',
            'ak_ai/static/src/js/kai_message.js',
            'ak_ai/static/src/js/kai_discuss_patch.js',
            'ak_ai/static/src/js/kai_form_patch.js',
            'ak_ai/static/src/xml/kai_chat_widget.xml',
            'ak_ai/static/src/xml/kai_conversation.xml',
            'ak_ai/static/src/xml/kai_message.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
```

**File: [`models/__init__.py`](addons-custom/ak_ai/models/__init__.py)**
```python
from . import ak_ai_assistant
from . import ak_ai_conversation
from . import ak_ai_message
from . import ak_ai_prompt_template
from . import ak_ai_usage_log
from . import ak_ai_mixin
from . import discuss_channel
from . import res_partner
from . import res_users
```

**File: [`models/ak_ai_conversation.py`](addons-custom/ak_ai/models/ak_ai_conversation.py)**
```python
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class AkAiConversation(models.Model):
    _name = 'ak_ai.conversation'
    _description = 'KAI Conversation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'last_message_date desc, id desc'
    
    name = fields.Char('Title', compute='_compute_name', store=True, tracking=True)
    user_id = fields.Many2one('res.users', 'User', required=True, 
                              default=lambda self: self.env.user, tracking=True)
    
    # Access Mode
    access_mode = fields.Selection([
        ('discuss', 'Discuss Channel'),
        ('chatter', 'Chatter/Form'),
        ('both', 'Both'),
        ('api', 'API')
    ], string='Access Mode', default='discuss', required=True, tracking=True)
    
    # Discuss Integration
    channel_id = fields.Many2one('discuss.channel', 'Discuss Channel', tracking=True)
    
    # Context
    context_mode = fields.Selection([
        ('general', 'General Chat'),
        ('record', 'Single Record'),
        ('multi', 'Multiple Records'),
        ('search', 'Search Results')
    ], string='Context Mode', default='general', required=True, tracking=True)
    
    context_model = fields.Char('Context Model')
    context_res_id = fields.Integer('Context Record ID')
    context_res_ids = fields.Text('Multiple Record IDs (JSON)')
    context_data = fields.Text('Cached Context Data (JSON)')
    
    # Messages
    message_ids = fields.One2many('ak_ai.message', 'conversation_id', 'Messages')
    message_count = fields.Integer('Message Count', compute='_compute_message_count', store=True)
    
    # State
    state = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archived')
    ], default='active', required=True, tracking=True)
    
    # Metadata
    create_date = fields.Datetime('Created', readonly=True)
    last_message_date = fields.Datetime('Last Message', tracking=True)
    
    # Stats
    total_tokens_used = fields.Integer('Total Tokens', compute='_compute_stats', store=True)
    estimated_cost = fields.Float('Estimated Cost', compute='_compute_stats', store=True)
    
    @api.depends('message_ids')
    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.message_ids)
    
    @api.depends('message_ids.tokens_used')
    def _compute_stats(self):
        for record in self:
            record.total_tokens_used = sum(record.message_ids.mapped('tokens_used'))
            # Rough estimate: $0.03/1K tokens
            record.estimated_cost = (record.total_tokens_used / 1000) * 0.03
    
    @api.depends('context_model', 'context_res_id', 'user_id', 'create_date')
    def _compute_name(self):
        for record in self:
            if record.context_mode == 'record' and record.context_model:
                try:
                    res = self.env[record.context_model].browse(record.context_res_id)
                    record.name = f"KAI - {res.display_name}"
                except:
                    record.name = f"KAI - {record.context_model}"
            else:
                record.name = f"KAI Chat - {record.user_id.name}"
    
    def switch_to_context(self, model, res_id):
        """Switch from general to contextual mode"""
        self.ensure_one()
        
        self.write({
            'context_mode': 'record',
            'context_model': model,
            'context_res_id': res_id,
            'access_mode': 'both'
        })
        
        # Add system message
        self.env['ak_ai.message'].create({
            'conversation_id': self.id,
            'role': 'system',
            'content': f'Context loaded: {model} (ID: {res_id})',
        })
        
        return self.prepare_context()
    
    def prepare_context(self):
        """Prepare context based on mode"""
        self.ensure_one()
        
        if self.context_mode == 'general':
            return self._prepare_general_context()
        elif self.context_mode == 'record':
            return self._prepare_record_context()
        elif self.context_mode == 'multi':
            return self._prepare_multi_record_context()
        
        return {}
    
    def _prepare_general_context(self):
        """General context without specific record"""
        return {
            'mode': 'general',
            'user': {
                'id': self.env.user.id,
                'name': self.env.user.name,
                'lang': self.env.user.lang,
                'tz': self.env.user.tz,
            },
            'company': {
                'id': self.env.company.id,
                'name': self.env.company.name,
                'currency': self.env.company.currency_id.name,
            }
        }
    
    def _prepare_record_context(self):
        """Load full record context"""
        if not self.context_model or not self.context_res_id:
            return self._prepare_general_context()
        
        try:
            model = self.env[self.context_model]
            record = model.browse(self.context_res_id)
            
            if not record.exists():
                return self._prepare_general_context()
            
            # Check access
            record.check_access_rights('read')
            record.check_access_rule('read')
            
            # Custom context method
            if hasattr(record, '_prepare_kai_context'):
                context = record._prepare_kai_context()
            else:
                context = self._prepare_generic_context(record)
            
            # Cache context
            self.context_data = json.dumps(context)
            
            return context
            
        except Exception as e:
            _logger.error(f"Error preparing context: {e}")
            return self._prepare_general_context()
    
    def _prepare_generic_context(self, record):
        """Generic context for any model"""
        return {
            'mode': 'record',
            'model': record._name,
            'model_description': record._description,
            'id': record.id,
            'display_name': record.display_name,
            'fields': self._get_accessible_fields(record),
            'user_permissions': {
                'read': True,
                'write': record.check_access_rights('write', raise_exception=False),
                'create': record.check_access_rights('create', raise_exception=False),
                'unlink': record.check_access_rights('unlink', raise_exception=False),
            }
        }
    
    def _get_accessible_fields(self, record):
        """Get accessible fields for the record"""
        accessible = {}
        
        for fname, field in record._fields.items():
            if fname.startswith('_') or field.type == 'binary':
                continue
            
            try:
                value = record[fname]
                
                if field.type == 'many2one':
                    accessible[fname] = {'id': value.id, 'name': value.display_name} if value else None
                elif field.type in ['one2many', 'many2many']:
                    accessible[fname] = [{'id': r.id, 'name': r.display_name} for r in value[:10]]
                elif field.type in ['date', 'datetime']:
                    accessible[fname] = str(value) if value else None
                elif field.type == 'selection':
                    accessible[fname] = dict(field.selection).get(value, value)
                else:
                    accessible[fname] = value
            except:
                continue
        
        return accessible
    
    def action_archive(self):
        """Archive conversation"""
        self.write({'state': 'archived'})
    
    def action_activate(self):
        """Activate conversation"""
        self.write({'state': 'active'})
```

#### 1.3 Security Setup

**File: [`security/ak_ai_security.xml`](addons-custom/ak_ai/security/ak_ai_security.xml)**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Groups -->
    <record id="group_kai_user" model="res.groups">
        <field name="name">KAI User</field>
        <field name="category_id" ref="base.module_category_productivity"/>
        <field name="comment">Can use KAI assistant</field>
    </record>
    
    <record id="group_kai_manager" model="res.groups">
        <field name="name">KAI Manager</field>
        <field name="category_id" ref="base.module_category_productivity"/>
        <field name="implied_ids" eval="[(4, ref('group_kai_user'))]"/>
        <field name="comment">Can manage KAI configuration</field>
    </record>
    
    <!-- Record Rules -->
    <record id="ak_ai_conversation_user_rule" model="ir.rule">
        <field name="name">KAI Conversation: User Access</field>
        <field name="model_id" ref="model_ak_ai_conversation"/>
        <field name="groups" eval="[(4, ref('group_kai_user'))]"/>
        <field name="domain_force">[('user_id', '=', user.id)]</field>
    </record>
    
    <record id="ak_ai_conversation_manager_rule" model="ir.rule">
        <field name="name">KAI Conversation: Manager Access</field>
        <field name="model_id" ref="model_ak_ai_conversation"/>
        <field name="groups" eval="[(4, ref('group_kai_manager'))]"/>
        <field name="domain_force">[(1, '=', 1)]</field>
    </record>
</odoo>
```

**File: [`security/ir.model.access.csv`](addons-custom/ak_ai/security/ir.model.access.csv)**
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_kai_conversation_user,ak_ai.conversation user,model_ak_ai_conversation,group_kai_user,1,1,1,1
access_kai_message_user,ak_ai.message user,model_ak_ai_message,group_kai_user,1,1,1,0
access_kai_assistant_user,ak_ai.assistant user,model_ak_ai_assistant,group_kai_user,1,0,0,0
access_kai_prompt_template_user,ak_ai.prompt_template user,model_ak_ai_prompt_template,group_kai_user,1,0,0,0
access_kai_usage_log_user,ak_ai.usage_log user,model_ak_ai_usage_log,group_kai_user,1,0,0,0
access_kai_assistant_manager,ak_ai.assistant manager,model_ak_ai_assistant,group_kai_manager,1,1,1,1
access_kai_prompt_template_manager,ak_ai.prompt_template manager,model_ak_ai_prompt_template,group_kai_manager,1,1,1,1
access_kai_usage_log_manager,ak_ai.usage_log manager,model_ak_ai_usage_log,group_kai_manager,1,1,1,1
```

### Phase 2: Discuss Integration (Week 2)

#### 2.1 Bot User Creation

**File: [`data/ak_ai_data.xml`](addons-custom/ak_ai/data/ak_ai_data.xml)**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- KAI Bot Partner -->
    <record id="partner_kai_bot" model="res.partner">
        <field name="name">KAI</field>
        <field name="email">kai@kardan.digital</field>
        <field name="company_id" eval="False"/>
        <field name="active">True</field>
        <field name="type">contact</field>
        <field name="comment">Kardan AI Assistant Bot</field>
    </record>
    
    <!-- KAI Bot User -->
    <record id="user_kai_bot" model="res.users">
        <field name="name">KAI Assistant</field>
        <field name="login">kai_bot</field>
        <field name="partner_id" ref="partner_kai_bot"/>
        <field name="active">True</field>
        <field name="groups_id" eval="[(6, 0, [ref('base.group_system')])]"/>
        <field name="share">False</field>
        <field name="notification_type">inbox</field>
    </record>
</odoo>
```

### Phase 3: Chatter Integration (Week 3)

**File: [`models/ak_ai_mixin.py`](addons-custom/ak_ai/models/ak_ai_mixin.py)** - Already detailed above

### Phase 4: AI Services (Week 4)

**File: [`services/openai_service.py`](addons-custom/ak_ai/services/openai_service.py)** - OpenAI integration

### Phase 5: Frontend (Week 5-6)

**File: [`static/src/js/kai_chat_widget.js`](addons-custom/ak_ai/static/src/js/kai_chat_widget.js)** - Chat widget

### Phase 6: Testing & Polish (Week 7)

## Development Checklist

```markdown
### Module Setup
- [ ] Create directory structure
- [ ] Initialize __init__.py files
- [ ] Create __manifest__.py
- [ ] Install required Python packages

### Models
- [ ] ak_ai.conversation model
- [ ] ak_ai.message model
- [ ] ak_ai.assistant model
- [ ] ak_ai.prompt_template model
- [ ] ak_ai.usage_log model
- [ ] ak_ai.mixin for inheritance

### Security
- [ ] Create security groups
- [ ] Define access rights (CSV)
- [ ] Create record rules
- [ ] Implement field-level security

### Data
- [ ] KAI bot user/partner
- [ ] Default prompt templates
- [ ] System parameters
- [ ] Cron jobs

### Views
- [ ] Conversation views (tree, form, kanban)
- [ ] Message views
- [ ] Settings page
- [ ] Menus

### Discuss Integration
- [ ] Inherit discuss.channel
- [ ] Auto-create KAI channel
- [ ] Message interception
- [ ] Response generation

### Chatter Integration
- [ ] Create mixin
- [ ] Apply to models (sale, purchase, invoice)
- [ ] Smart button
- [ ] Context preparation

### AI Services
- [ ] Base service class
- [ ] OpenAI integration
- [ ] Anthropic integration
- [ ] Error handling

### Frontend
- [ ] Chat widget component
- [ ] Conversation UI
- [ ] Message formatting
- [ ] CSS styling

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] UI tests

### Documentation
- [ ] README.md
- [ ] User guide
- [ ] Developer guide
- [ ] Deployment guide

### Deployment
- [ ] Demo data
- [ ] Translations (TR/EN)
- [ ] Icon and banner
- [ ] Performance optimization
```

## Next Steps

Would you like me to:
1. Start implementing the code (switch to Code mode)?
2. Create more detailed designs for specific components?
3. Create mockups for the UI?
4. Discuss any specific technical requirements?
