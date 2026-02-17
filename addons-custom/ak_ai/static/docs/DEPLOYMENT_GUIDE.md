# KAI - Deployment Guide

> **Module:** ak_ai (KAI - Kardan AI Assistant)
> **Odoo Version:** 18.0
> **Document Revision:** 1.0 | 2026-02-17

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [AI Provider Setup](#3-ai-provider-setup)
4. [Security & Access Control](#4-security--access-control)
5. [Chatter Integration](#5-chatter-integration)
6. [Discuss Channel Setup](#6-discuss-channel-setup)
7. [Scheduled Tasks](#7-scheduled-tasks)
8. [Production Checklist](#8-production-checklist)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

### System Requirements

| Requirement | Details |
|-------------|---------|
| Odoo | 18.0 (Community or Enterprise) |
| Python | 3.10+ |
| Odoo Modules | `base`, `web`, `mail`, `contacts`, `sale`, `purchase`, `account` |

### Python Dependencies

```bash
pip install openai anthropic tiktoken
```

Verify installation:

```bash
python3 -c "import openai, anthropic, tiktoken; print('OK')"
```

### API Key (at least one required)

| Provider | Key Source |
|----------|-----------|
| OpenAI | https://platform.openai.com/api-keys |
| Anthropic | https://console.anthropic.com/settings/keys |
| OpenRouter | https://openrouter.ai/keys |
| Local LLM | No key needed (Ollama, LM Studio, etc.) |

---

## 2. Installation

### 2.1 Copy Module

```bash
cp -r ak_ai /path/to/odoo/addons-custom/
```

Ensure `addons-custom` is in Odoo's `addons_path` in `odoo.conf`:

```ini
addons_path = /opt/odoo18/odoo/addons,/opt/odoo18/addons-custom
```

### 2.2 Restart and Update

```bash
# Restart Odoo
sudo systemctl restart odoo

# OR update via command line
./odoo-bin -u ak_ai -d YOUR_DATABASE --stop-after-init
```

### 2.3 Activate Module

1. Go to **Apps** menu
2. Remove "Apps" filter, search for `KAI`
3. Click **Install**

After installation, a default AI assistant record is automatically created via `data/ak_ai_data.xml`.

---

## 3. AI Provider Setup

Navigate to: **KAI > Configuration > AI Assistants**

### 3.1 Provider Configuration

| Field | Description | Default |
|-------|-------------|---------|
| Name | Display name | KAI - Kardan AI Assistant |
| Status | Active / Inactive | Active |
| AI Provider | openai / anthropic / openrouter / local | openai |
| Mode | chat (stateless) / assistants (stateful threads) | chat |
| Model Name | Model identifier | gpt-4o-mini |
| API Key | Provider API key (admin-only field) | - |
| API Base URL | Provider endpoint | Auto-set per provider |

### 3.2 Default Models by Provider

| Provider | Default Model | API Base URL |
|----------|--------------|--------------|
| OpenAI | gpt-4o-mini | https://api.openai.com/v1 |
| Anthropic | claude-3-5-sonnet-20241022 | https://api.anthropic.com |
| OpenRouter | anthropic/claude-3.5-haiku | https://openrouter.ai/api/v1 |
| Local LLM | llama-3.2 | http://localhost:11434/v1 |

### 3.3 Response Tuning

| Parameter | Default | Recommendation |
|-----------|---------|----------------|
| Max Tokens | 4000 | 2000-4000 for general, 4000-8000 for code |
| Temperature | 0.3 | 0.2-0.3 for accuracy, 0.7-0.9 for creative |
| Rate Limit | 100/hour | Adjust per user load |

### 3.4 Assistants API Mode (Optional)

For OpenAI's stateful Assistants API:

1. Set **Mode** to `assistants`
2. Create an Assistant at https://platform.openai.com/assistants
3. Enter the **AI Assistant ID** (e.g., `asst_abc123...`)
4. Thread management is handled automatically per conversation

---

## 4. Security & Access Control

### 4.1 Security Groups

| Group | XML ID | Purpose |
|-------|--------|---------|
| KAI User | `ak_ai.group_ak_ai_user` | Can use KAI, see own conversations |
| KAI Manager | `ak_ai.group_ak_ai_manager` | Full config, all logs, knowledge management |
| System Admin | `base.group_system` | Auto-included as KAI User, API key access |

System Admins are automatically added to the KAI User group.

### 4.2 Assign Users

**Option A - Group-based:**

Settings > Users & Companies > Users > Select user > Access Rights tab > Add to KAI User group

**Option B - Assistant-level (fine-grained):**

KAI > Configuration > AI Assistants > "Access Control" tab:
- **Allowed Users**: Specific users
- **Allowed Groups**: Specific security groups

If both are empty, all KAI Users have access.

### 4.3 Record-Level Security (Auto-applied)

| Data | Rule |
|------|------|
| Conversations | Users see only their own |
| Messages | Users see only their own conversation messages |
| Interaction Logs | Users see only their own logs |
| Learning Records | Users see only their own feedback |
| All records | KAI Managers and System Admins see everything |

### 4.4 API Key Security

- API keys are only visible to **System Administrators** (`base.group_system`)
- Keys are never exposed in Chatter, logs, or regular user views

---

## 5. Chatter Integration

To add "Ask KAI" button to any business model:

### 5.1 Add Mixin to Model

In your custom module's model:

```python
from odoo import models

class SaleOrder(models.Model):
    _inherit = ['sale.order', 'ak_ai.mixin']
```

### 5.2 Add Dependency

In your custom module's `__manifest__.py`:

```python
'depends': ['sale', 'ak_ai'],
```

### 5.3 Verify

1. Navigate to a Sale Order form
2. The "Ask KAI" button appears near the Chatter
3. Click to open AI chat with full record context

For a quick reference, see [CHATTER_QUICK_FIX_TR.md](./CHATTER_QUICK_FIX_TR.md).

---

## 6. Discuss Channel Setup

KAI can also operate as a bot in Odoo Discuss:

### 6.1 Automatic

If configured in the module, a KAI channel is created during installation.

### 6.2 Manual (Odoo Shell)

```python
env['discuss.channel'].create_ai_channel(name="KAI Assistant")
```

### 6.3 How It Works

1. User sends a message in the KAI channel
2. `_message_post_after_hook` intercepts the message
3. Creates/resumes an `ak_ai.conversation`
4. AI response is posted back to the channel

---

## 7. Scheduled Tasks

### 7.1 Log Cleanup (Recommended)

Configure a cron job to clean old interaction logs:

Settings > Technical > Automation > Scheduled Actions > Create:

| Field | Value |
|-------|-------|
| Name | KAI: Cleanup Old Logs |
| Model | ak_ai.interaction_log |
| Method | cleanup_old_logs |
| Arguments | `(90,)` (days to keep) |
| Interval | 1 Week |

### 7.2 Knowledge Rebuild (Optional)

To periodically refresh knowledge base:

| Field | Value |
|-------|-------|
| Name | KAI: Rebuild Knowledge |
| Model | ak_ai.knowledge_builder |
| Method | build_all_knowledge |
| Interval | 1 Day |

---

## 8. Production Checklist

### Pre-Go-Live

- [ ] Python dependencies installed (`openai`, `anthropic`, `tiktoken`)
- [ ] Module installed and updated without errors
- [ ] AI Provider configured with valid API key
- [ ] Test API connection (send a test message)
- [ ] Security groups assigned to appropriate users
- [ ] Rate limits configured (default: 100/hour)
- [ ] Temperature set to 0.3 for production accuracy
- [ ] Max tokens set to 4000 (balance cost vs. response quality)

### Security

- [ ] API keys entered only by System Admin
- [ ] Verify record rules: users see only own conversations
- [ ] No sudo operations enabled (module enforces user-level access)
- [ ] Interaction logs enabled for audit trail

### Monitoring

- [ ] Log cleanup cron scheduled
- [ ] Check interaction logs for token usage and costs
- [ ] Monitor rate limit hits in server logs
- [ ] Review user feedback in Learning records

### Backup

- [ ] Odoo database backup includes `ak_ai.*` tables
- [ ] API keys documented in secure password manager (not in code)

---

## 9. Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "No active AI assistant found" | No assistant record or all inactive | Create/activate an assistant in KAI > Configuration |
| 401 Unauthorized | Invalid API key | Verify API key in assistant configuration |
| 402 Payment Required | Provider credits exhausted | Top up credits on provider dashboard |
| 429 Rate Limited | Too many requests | Increase rate limit or wait |
| Empty AI response | Max tokens too low | Increase max_tokens (try 4000) |
| "Access Denied" on chat | User not in KAI User group | Add user to `ak_ai.group_ak_ai_user` |
| "Ask KAI" button missing | Mixin not added to model | Inherit `ak_ai.mixin` on target model |
| Code execution fails | User lacks permission on target records | Verify user's Odoo access rights |
| Slow responses | Large context or slow provider | Reduce related record limits or switch provider |

### Useful Shell Commands

For debugging via Odoo shell (`./odoo-bin shell -d DB`):

```python
# Check active assistant
env['ak_ai.assistant'].get_active_assistant()

# Check user access
env['ak_ai.assistant'].get_active_assistant().check_user_access()

# List conversations
env['ak_ai.conversation'].search([('user_id', '=', env.uid)])

# Check interaction logs
env['ak_ai.interaction_log'].search_count([])
```

For more shell commands, see [SHELL_COMMANDS.md](./SHELL_COMMANDS.md).

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-17 | Initial deployment guide |

---

Kardan.Digital - Intelligent Odoo Solutions
