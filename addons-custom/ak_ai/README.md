# AK_AI (KAI) - Complete Design Documentation

## 📋 Executive Summary

**KAI (Kardan AI)** is an intelligent AI assistant addon for Odoo 18 that provides contextual help, task automation, and intelligent guidance directly within the Odoo interface. Similar to how Roo Code assists developers, KAI helps Odoo users work more efficiently.

## 🎯 Project Overview

- **Module Name**: `ak_ai`
- **Brand Name**: KAI (Kardan AI)
- **Version**: 1.1
- **License**: LGPL-3
- **Author**: Kardan.Digital

## 📚 Design Documents

### 1. [Core Design](./ak_ai_design.md)
Main design document covering system architecture, database models, and core capabilities.

### 2. [Integration Strategy](./ak_ai_integration_strategy.md)
Detailed integration approach:
- **Discuss Integration**: AI bot channel for general assistance
- **Chatter Integration**: Context-aware help on record forms
- **Hybrid Approach**: Best of both worlds
- User experience flows and security considerations

### 3. [Final Design](./ak_ai_final_design.md)
Complete technical specification including unified conversation models and AI service integration.

### 4. [Implementation Plan](./ak_ai_implementation_plan.md)
Step-by-step development guide and phase-by-phase implementation details.

### 5. [Learning Strategy](./ak_ai_learning_strategy.md)
How KAI learns and improves through context, feedback, and knowledge base systems.

### 6. [Comprehensive Knowledge](./ak_ai_comprehensive_knowledge.md)
Complete knowledge builder covering Odoo models, fields, views, and business data.

### 7. [Action Execution](./ak_ai_action_execution.md) ⭐
How KAI executes actions, navigates screens, and performs semantic verification of results.

### 8. [Intelligent Suggestions](./ak_ai_intelligent_suggestions.md) ⭐
How KAI generates smart action suggestions using function calling and dynamic tool use.

### 9. [Dynamic Tool System](./ak_ai_dynamic_tools.md) ⭐⭐
Extensible tool architecture where tools are stored in the database and can be added by any module.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
├──────────────────────┬──────────────────────────────────────┤
│   Discuss Channel    │        Chatter Integration           │
│   🤖 KAI Assistant   │    Smart Button "Ask KAI"            │
└──────────────────────┴──────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  ak_ai.conversation                          │
│  (Unified conversation management with context awareness)   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│   Context        │  AI Service      │   Knowledge Base     │
│   Loader         │  Layer           │   System             │
├──────────────────┼──────────────────┼──────────────────────┤
│ • Record Data    │ • OpenAI API     │ • Odoo Metadata      │
│ • User Info      │ • Anthropic API  │ • User Patterns      │
│ • Permissions    │ • OpenRouter     │ • Learning Examples  │
│ • Related Data   │ • Local LLM      │ • Company Knowledge  │
└──────────────────┴──────────────────┴──────────────────────┘
```

## 🌟 Key Features

### Dual Integration
- ✅ **Discuss Channel**: General AI chat accessible from Discuss app
- ✅ **Chatter Integration**: Context-aware assistance on forms
- ✅ **Seamless Switching**: Move between general and contextual modes

### Context Intelligence
- ✅ **Full Record Access**: Reads all fields user can access
- ✅ **Related Records**: Understands connections (lines, invoices, etc.)
- ✅ **User Awareness**: Knows user permissions and preferences
- ✅ **Business Context**: Understands workflows and processes

### Learning System
- ✅ **Automatic Learning**: Learns Odoo structure automatically
- ✅ **User Feedback**: Improves from thumbs up/down
- ✅ **Knowledge Base**: Company-specific articles and FAQs
- [ ] **Continuous Improvement**: Daily analysis and optimization (Planned)

### Comprehensive Knowledge
KAI knows about:
- All models, fields, and views in Odoo
- Users, groups, and permission structure
- Companies, teams, and departments
- System configuration and parameters
- Business data (partners, products, currencies)
- External integrations and APIs
- Custom and installed modules
- Workflows and state transitions

## 🔒 Security & Audit Features

- ✅ **Audit Trail**: Logs all AI interactions with detailed token usage (Input/Output/Total) and cost tracking.
- ✅ **Cost Management**: Interaction costs are tracked per request and visible only to **System Administrators**.
- ✅ **Semantic Safety**: AI code execution includes mandatory verification steps and semantic checks to prevent logical errors (e.g., creating records with zero prices).
- ✅ **Access Control**: Strictly respects Odoo's security model (ACLs and Record Rules).
- ✅ **Data Privacy**: Filtered context and sensitive data masking.
- ✅ **Encryption**: API keys and sensitive data are encrypted at rest.
- ✅ **GDPR Compliant**: Data retention policies.

## 📊 Use Cases

### 1. Help & Guidance
```
User: "How do I create a sales order?"
KAI: "I'll guide you step by step:
1. Go to Sales → Orders → Quotations
2. Click 'Create'
3. Select customer...
Would you like me to navigate you there?"
```

### 2. Context-Aware Assistance
```
User: (on Sale Order SO001) "Why can't I invoice this?"
KAI: "I see the issue with SO001:
• State: Draft (needs to be confirmed first)
• Click 'Confirm' to change status
• Then you can create invoices
Shall I explain the confirmation process?"
```

### 3. Task Automation with Safety
```
User: "Create invoice for this order"
KAI: "I can create an invoice for SO001:
• Customer: Acme Corp
• Amount: $1,234.56
• Full invoice (100%)

[EXECUTE_CODE]
# KAI generates code with semantic checks
[/EXECUTE_CODE]

KAI Summary: "Invoice INV/2025/001 created successfully for $1,234.56. Verified: Price and customer match SO001."
```

## 🎓 Learning Capabilities

### What KAI Learns Automatically
1. **Odoo Structure**: Models, fields, views, menus
2. **Security**: Users, groups, permissions, record rules
3. **Organization**: Companies, teams, departments
4. **Configuration**: Settings, parameters
5. **Business Data**: Partners, products, currencies
6. **Integrations**: APIs, webhooks, cron jobs
7. **Custom Modules**: Installed and custom addons

### How KAI Improves
1. **User Feedback**: Learns from ratings and corrections
2. **Usage Patterns**: Understands common workflows
3. **Knowledge Base**: Stores company-specific information
4. **RAG System**: Retrieves relevant knowledge
5. [ ] **A/B Testing**: Tests different prompt variations (Planned)
6. [ ] **Continuous Learning**: Daily knowledge refresh (Planned)

## 🚀 Implementation Status

### Phase 1: Foundation (Completed)
- Module structure and core models
- Security setup
- Basic configuration

### Phase 2: Discuss Integration (Completed)
- Create AI bot user/partner
- Discuss channel creation
- Message interception and response

### Phase 3: Chatter Integration (Completed)
- Create mixin for models
- Context preparation system
- Smart button implementation

### Phase 4: AI Services (Completed)
- OpenAI integration
- Anthropic integration
- OpenRouter integration
- Error handling and fallbacks

### Phase 5: Frontend (Completed)
- Chat widget (JavaScript/Owl)
- Conversation UI
- Message formatting

### Phase 6: Learning System (In Progress)
- ✅ Knowledge builder
- ✅ Feedback system
- [ ] Continuous improvement (Planned)

### Phase 7: Testing & Polish (Ongoing)
- ✅ Unit tests
- ✅ Integration tests
- ✅ UI/UX refinements
- ✅ Documentation

## 📁 File Structure

```
addons-custom/ak_ai/
├── __init__.py
├── __manifest__.py
├── README.md
│
├── models/
│   ├── ak_ai_assistant.py           # Configuration and provider settings
│   ├── ak_ai_conversation.py        # Main conversation model
│   ├── ak_ai_message.py             # Message history
│   ├── ak_ai_interaction_log.py     # Detailed audit logs (Tokens, Cost, Time)
│   ├── ak_ai_knowledge_builder.py   # Knowledge system
│   ├── ak_ai_mixin.py               # Mixin for chatter integration
│   └── discuss_channel.py           # Discuss app integration
│
├── services/
│   ├── base_ai_service.py           # Base logic and security rules
│   ├── openai_service.py            # OpenAI integration
│   ├── anthropic_service.py         # Anthropic integration
│   └── openrouter_service.py        # OpenRouter (multi-model) integration
│
├── views/
│   ├── ak_ai_assistant_views.xml
│   ├── ak_ai_conversation_views.xml
│   ├── ak_ai_knowledge_views.xml    # Includes Interaction Log views
│   └── menu.xml
│
├── static/src/
│   ├── js/                          # Owl components and chat widgets
│   ├── xml/                         # Owl templates
│   ├── css/                         # Styling
│   └── img/                         # Icons and assets
│
├── security/
│   ├── ir.model.access.csv
│   └── ak_ai_security.xml
│
└── data/
    └── ak_ai_data.xml               # Bot user and system parameters
```

## 🛠️ Development Requirements

### Python Dependencies
```
openai>=1.0.0
anthropic>=0.7.0
requests
```

### Odoo Dependencies
```
base, web, mail, contacts
```

## 🔮 Future Roadmap
- [ ] **Voice Interface**: Speech-to-text for hands-free operation.
- [ ] **Proactive Suggestions**: AI-driven alerts based on user behavior.
- [ ] **Local LLM Support**: Full integration for offline/private AI models.
- [ ] **Multi-step Workflows**: Complex automation spanning multiple modules.

## 🤝 Support

For questions or issues, contact: support@kardan.digital

---
© 2025 Kardan.Digital - Intelligent Odoo Solutions
