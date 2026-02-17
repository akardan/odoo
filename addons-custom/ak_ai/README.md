# AK_AI (KAI) - Complete Design Documentation

## Executive Summary

**KAI (Kardan AI)** is an intelligent AI assistant addon for Odoo 18 that provides contextual help, task automation, and intelligent guidance directly within the Odoo interface. Similar to how Roo Code assists developers, KAI helps Odoo users work more efficiently.

## Project Overview

- **Module Name**: `ak_ai`
- **Brand Name**: KAI (Kardan AI)
- **Version**: 18.0.1.0.0
- **License**: OPL-1
- **Author**: Kardan.Digital
- **Category**: Productivity
- **Application**: Yes

## Quick Start

| Role | Document |
|------|----------|
| System Admin / DevOps | [Deployment Guide](./static/docs/DEPLOYMENT_GUIDE.md) |
| Son Kullanici (TR) | [Kullanim Kilavuzu](./static/docs/KULLANIM_KILAVUZU_TR.md) |
| Developer | Design Documents (below) |

## Design Documents

### 1. [Core Design](./static/docs/ak_ai_design.md)
Main design document covering system architecture, database models, and core capabilities.

### 2. [Integration Strategy](./static/docs/ak_ai_integration_strategy.md)
Detailed integration approach: Discuss, Chatter, and hybrid approaches.

### 3. [Final Design](./static/docs/ak_ai_final_design.md)
Complete technical specification including unified conversation models and AI service integration.

### 4. [Implementation Plan](./static/docs/ak_ai_implementation_plan.md)
Step-by-step development guide and phase-by-phase implementation details.

### 5. [Learning Strategy](./static/docs/ak_ai_learning_strategy.md)
How KAI learns and improves through context, feedback, and knowledge base systems.

### 6. [Comprehensive Knowledge](./static/docs/ak_ai_comprehensive_knowledge.md)
Complete knowledge builder covering Odoo models, fields, views, and business data.

### 7. [Action Execution](./static/docs/ak_ai_action_execution.md)
How KAI executes actions, navigates screens, and performs semantic verification of results.

### 8. [Intelligent Suggestions](./static/docs/ak_ai_intelligent_suggestions.md)
Smart action suggestions using function calling and dynamic tool use.

### 9. [Dynamic Tool System](./static/docs/ak_ai_dynamic_tools.md)
Extensible tool architecture where tools are stored in the database and can be added by any module.

### 10. [Security Principles](./static/docs/ak_ai_security_principles.md)
Security architecture, user-permission-based operations, and safety rules.

### 11. [Dynamic Code Execution](./static/docs/ak_ai_dynamic_code_execution.md)
How KAI safely generates and executes code with semantic verification.

### 12. [Data Extraction & Creation](./static/docs/ak_ai_data_extraction_and_creation.md)
Strategies for reading and writing Odoo data through AI interactions.

### 13. [OpenRouter Guide](./static/docs/README_OPENROUTER.md)
OpenRouter multi-model integration setup and usage.

## Architecture Overview

```
+-------------------------------------------------------------+
|                        User Interface                        |
+----------------------+--------------------------------------+
|   Discuss Channel    |        Chatter Integration           |
|   KAI Assistant      |    Smart Button "Ask KAI"            |
+----------------------+--------------------------------------+
                              |
+-------------------------------------------------------------+
|                  ak_ai.conversation                          |
|  (Unified conversation management with context awareness)   |
+-------------------------------------------------------------+
                              |
+------------------+------------------+------------------------+
|   Context        |  AI Service      |   Knowledge Base       |
|   Loader         |  Layer           |   System               |
+------------------+------------------+------------------------+
| - Record Data    | - OpenAI API     | - Odoo Metadata        |
| - User Info      | - Anthropic API  | - User Patterns        |
| - Permissions    | - OpenRouter     | - Learning Examples    |
| - Related Data   | - Local LLM      | - Company Knowledge    |
+------------------+------------------+------------------------+
```

## Key Features

### Dual Integration
- **Discuss Channel**: General AI chat accessible from Discuss app
- **Chatter Integration**: Context-aware assistance on forms via Smart Button
- **Seamless Switching**: Move between general and contextual modes

### Context Intelligence
- **Full Record Access**: Reads all fields user can access
- **Related Records**: Understands connections (lines, invoices, etc.)
- **User Awareness**: Knows user permissions and preferences
- **Business Context**: Understands workflows and processes

### Learning System
- **Automatic Learning**: Learns Odoo structure automatically
- **User Feedback**: Improves from thumbs up/down
- **Knowledge Base**: Company-specific articles and FAQs
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

## Security & Audit Features

- **Audit Trail**: Logs all AI interactions with detailed token usage (Input/Output/Total) and cost tracking.
- **Cost Management**: Interaction costs are tracked per request and visible only to **System Administrators**.
- **Semantic Safety**: AI code execution includes mandatory verification steps and semantic checks to prevent logical errors (e.g., creating records with zero prices).
- **Access Control**: Strictly respects Odoo's security model (ACLs and Record Rules). No sudo operations.
- **Data Privacy**: Filtered context and sensitive data masking.
- **Encryption**: API keys and sensitive data are encrypted at rest.

## Use Cases

### 1. Help & Guidance
```
User: "How do I create a sales order?"
KAI: "I'll guide you step by step:
1. Go to Sales > Orders > Quotations
2. Click 'Create'
3. Select customer...
Would you like me to navigate you there?"
```

### 2. Context-Aware Assistance
```
User: (on Sale Order SO001) "Why can't I invoice this?"
KAI: "I see the issue with SO001:
- State: Draft (needs to be confirmed first)
- Click 'Confirm' to change status
- Then you can create invoices
Shall I explain the confirmation process?"
```

### 3. Task Automation with Safety
```
User: "Create invoice for this order"
KAI: "I can create an invoice for SO001:
- Customer: Acme Corp
- Amount: $1,234.56
- Full invoice (100%)

[Executes with semantic verification]

KAI Summary: Invoice INV/2025/001 created successfully for $1,234.56.
Verified: Price and customer match SO001."
```

## Learning Capabilities

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

## Implementation Status

### Phase 1: Foundation (Completed)
- Module structure and core models
- Security setup (groups, ACLs, record rules)
- Basic configuration

### Phase 2: Discuss Integration (Completed)
- AI bot user/partner creation
- Discuss channel creation
- Message interception and response

### Phase 3: Chatter Integration (Completed)
- Mixin for models (`ak_ai_mixin.py`)
- Context preparation system
- Smart button implementation (`chatter_button.js` / `chatter_button.xml`)

### Phase 4: AI Services (Completed)
- OpenAI integration
- OpenAI Assistant (Threads) integration
- Anthropic integration
- OpenRouter integration
- Error handling and fallbacks

### Phase 5: Frontend (Completed)
- Chat widget (JavaScript/Owl)
- Conversation UI
- Message formatting

### Phase 6: Learning System (In Progress)
- Knowledge builder
- Feedback system
- Learning model (`ak_ai_learning.py`)
- [ ] Continuous improvement (Planned)

### Phase 7: Testing & Polish (Ongoing)
- Unit tests
- Integration tests
- UI/UX refinements
- Documentation

## File Structure

```
addons-custom/ak_ai/
|-- __init__.py
|-- __manifest__.py
|-- README.md
|
|-- models/
|   |-- __init__.py
|   |-- ak_ai_assistant.py           # Configuration and provider settings
|   |-- ak_ai_conversation.py        # Main conversation model
|   |-- ak_ai_message.py             # Message history
|   |-- ak_ai_interaction_log.py     # Detailed audit logs (Tokens, Cost, Time)
|   |-- ak_ai_knowledge_builder.py   # Knowledge system
|   |-- ak_ai_learning.py            # Learning and feedback model
|   |-- ak_ai_mixin.py               # Mixin for chatter integration
|   +-- discuss_channel.py           # Discuss app integration
|
|-- services/
|   |-- __init__.py
|   |-- base_ai_service.py           # Base logic and security rules
|   |-- openai_service.py            # OpenAI integration
|   |-- openai_assistant_service.py  # OpenAI Assistant (Threads) integration
|   |-- anthropic_service.py         # Anthropic integration
|   +-- openrouter_service.py        # OpenRouter (multi-model) integration
|
|-- controllers/
|   +-- main.py                      # HTTP endpoints and API controllers
|
|-- views/
|   |-- ak_ai_assistant_views.xml
|   |-- ak_ai_conversation_views.xml
|   |-- ak_ai_knowledge_views.xml    # Includes Interaction Log views
|   +-- menu.xml
|
|-- static/
|   |-- src/
|   |   |-- js/
|   |   |   |-- ak_ai_chat_widget.js # Main chat widget (Owl)
|   |   |   +-- chatter_button.js    # Chatter "Ask KAI" button
|   |   |-- xml/
|   |   |   |-- ak_ai_templates.xml  # Chat widget templates
|   |   |   +-- chatter_button.xml   # Chatter button template
|   |   |-- css/
|   |   |   +-- ak_ai.css            # Styling
|   |   +-- img/
|   |       +-- icon.png             # Module icon
|   |-- description/
|   |   |-- icon.png
|   |   +-- icon.webp
|   +-- docs/                        # Design & reference documentation
|       |-- ak_ai_design.md
|       |-- ak_ai_final_design.md
|       |-- ak_ai_integration_strategy.md
|       |-- ak_ai_implementation_plan.md
|       |-- ak_ai_learning_strategy.md
|       |-- ak_ai_comprehensive_knowledge.md
|       |-- ak_ai_action_execution.md
|       |-- ak_ai_intelligent_suggestions.md
|       |-- ak_ai_dynamic_tools.md
|       |-- ak_ai_dynamic_code_execution.md
|       |-- ak_ai_data_extraction_and_creation.md
|       |-- ak_ai_security_principles.md
|       +-- README_OPENROUTER.md
|
|-- security/
|   |-- ir.model.access.csv
|   +-- ak_ai_security.xml
|
|-- tests/
|   +-- test_basic_ai.py             # Unit and integration tests
|
+-- data/
    +-- ak_ai_data.xml               # Bot user and system parameters
```

## Development Requirements

### Python Dependencies
```
openai
anthropic
tiktoken
```

### Odoo Dependencies
```
base, web, mail, contacts, sale, purchase, account
```

## Future Roadmap
- [ ] **Voice Interface**: Speech-to-text for hands-free operation.
- [ ] **Proactive Suggestions**: AI-driven alerts based on user behavior.
- [ ] **Local LLM Support**: Full integration for offline/private AI models.
- [ ] **Multi-step Workflows**: Complex automation spanning multiple modules.

## Support

For questions or issues, contact: support@kardan.digital

---
Kardan.Digital - Intelligent Odoo Solutions
