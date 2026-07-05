# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an **Odoo 18 Community Edition** installation maintained by Kardan.Digital. The repository contains both the core Odoo framework and a suite of custom addons (`addons-custom/`) that extend it with domain-specific functionality, primarily in Turkish business contexts (procurement/tender management, exams, pharmaceutical, AI assistant).

## Repository Structure

```
/opt/odoo18/
├── odoo/                  # Core Odoo framework (upstream, do not modify)
├── addons/                # Standard Odoo community addons (upstream)
├── addons-custom/         # All custom Kardan.Digital addons (this is where we work)
├── odoo-bin               # Odoo CLI entry point
└── odoo.conf              # Local config (not used by systemd; see /etc/odoo.conf)
```

**Production config is at `/etc/odoo.conf`** — the database is `od18`, running on PostgreSQL at `localhost:5432`.

## Custom Addons (addons-custom/)

Several addons are **git submodules** with their own repositories on the `18.0` branch:

| Addon | Submodule Repo | Purpose |
|---|---|---|
| `ak_ai` | `akardan/kai` | KAI AI assistant (Claude/OpenAI/OpenRouter integration) |
| `ak_tender` | `akardan/tender` | Multi-stage procurement tender management (Turkish: İhale) |
| `ak_tender_mice` | `akardan/tender_mice` | MICE event tender extension (scenarios, shortlisting, counter-proposals) |
| `ak_workflow` | `akardan/workflow` | Generic multi-model workflow engine used by ak_tender |
| `ak_exams` | `akardan/exams` | Exam management system (extends Odoo Survey) |
| `ak_rpt` | `akardan/rpt` | Reference Price Tracking for pharma market access |
| `ak_open_badges` | `akardan/open_badges` | Digital certificates & Open Badges 2.0 |
| `ak_paytr` | `akardan/paytr` | PayTR payment gateway integration |
| `ak_eKT` | — (inline) | Electronic prospectus management for pharma (e-KT Hub) |
| `ak_branding` | — (inline) | White-label branding for Odoo UI |
| `ak_crm` | — (inline) | CRM extensions for pharmaceutical companies |
| `ak_exams` | — (inline) | Exam/survey management |
| `ak_learning` | — (inline) | eLearning extensions (random question ordering) |
| `ak_project` | — (inline) | Agile project management extensions |
| `ak_currency_rate_tcmb` | — (inline) | Turkish Central Bank exchange rate fetcher |

### Key Dependency Chain

```
ak_workflow ← ak_tender ← ak_tender_mice
ak_ai ← ak_tender (AI-enhanced purchase orders and requisitions)
ak_ai ← ak_exams (AI-enhanced survey analysis)
```

`ak_workflow` is a prerequisite for `ak_tender`. `ak_ai` is a dependency for both `ak_tender` and `ak_exams`.

## Service Management

```bash
# Start / Stop / Restart Odoo
sudo systemctl start odoo
sudo systemctl stop odoo
sudo systemctl restart odoo

# Check status and recent logs
sudo systemctl status odoo
sudo journalctl -u odoo -f          # live logs
sudo tail -f /var/log/odoo18.log    # file log

# Run Odoo manually (for debugging, stops the service first)
sudo systemctl stop odoo
sudo -u odoo /opt/odoo18-venv/bin/python3 /opt/odoo18/odoo-bin -c /etc/odoo.conf
```

The virtual environment is at `/opt/odoo18-venv/`. Always use its Python:

```bash
/opt/odoo18-venv/bin/python3
```

## Development Commands

### Install / Update a module

```bash
# Update a module (restarts Odoo after)
sudo -u odoo /opt/odoo18-venv/bin/python3 /opt/odoo18/odoo-bin \
  -c /etc/odoo.conf -d od18 -u ak_tender --stop-after-init

# Install a new module
sudo -u odoo /opt/odoo18-venv/bin/python3 /opt/odoo18/odoo-bin \
  -c /etc/odoo.conf -d od18 -i ak_tender --stop-after-init
```

### Run Tests

```bash
# Run tests for a specific addon
sudo -u odoo /opt/odoo18-venv/bin/python3 /opt/odoo18/odoo-bin \
  -c /etc/odoo.conf -d od18 --test-enable --stop-after-init -u ak_ai

# Run a single test class
sudo -u odoo /opt/odoo18-venv/bin/python3 /opt/odoo18/odoo-bin \
  -c /etc/odoo.conf -d od18 --test-enable --stop-after-init \
  --test-tags ak_ai.TestBasicAI -u ak_ai
```

Tests use `odoo.tests.common.TransactionCase` and are in each addon's `tests/` directory.

### Python Syntax Check

```bash
python3 /opt/odoo18/check_syntax.py
# Or check a specific file:
/opt/odoo18-venv/bin/python3 -m py_compile addons-custom/ak_ai/services/openrouter_service.py
```

### Submodule Updates

```bash
# Update a specific submodule
git submodule update --remote addons-custom/ak_tender

# Update all submodules
git submodule update --remote

# After changing a submodule, commit the pointer update from the main repo
git add addons-custom/ak_tender
git commit -m "chore: update submodule commit for ak_tender"
```

## Architecture Patterns

### Odoo Module Structure

Every addon follows standard Odoo conventions:
- `__manifest__.py` — module metadata, dependency list, data file loading order
- `models/` — Python model classes (`models.Model`, `models.AbstractModel`)
- `views/` — XML view definitions and menus
- `security/` — access control lists (`ir.model.access.csv`) and record rules
- `data/` — default/demo data loaded at install time
- `controllers/` — HTTP route handlers for portal/website features
- `static/` — frontend assets (JS, CSS, XML templates for OWL components)
- `wizards/` — transient models for multi-step dialogs

### Workflow Engine (ak_workflow)

`ak_workflow` provides a generic finite-state-machine system. To add workflow to any model, inherit the mixin:

```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['my.model', 'ak.workflow.mixin']
```

The mixin adds `workflow_definition_id`, `workflow_current_state_id`, and `workflow_available_transition_ids`. State transitions are defined in `ak.workflow.definition` records and support conditions (Python code), actions (email, method call, webhook), and multi-stage transitions.

`ak_tender.tender` inherits this mixin for its full tender lifecycle (draft → bidding → evaluation → award → closed).

### AI Integration (ak_ai)

`ak_ai` provides a provider-agnostic AI service layer. The pattern:
- `ak_ai.assistant` — configuration record (provider, model, API key, prompts)
- `ak_ai.service` (abstract) with concrete implementations: `ak_ai.service.openai`, `ak_ai.service.anthropic`, `ak_ai.service.openrouter`
- Models that need AI functionality inherit `ak_ai.mixin` or call `self.env['ak_ai.service'].get_service().generate_response(message, context)`

`ak_tender` uses this for AI-enhanced purchase order analysis (`purchase_order_ai.py`, `purchase_requisition_ai.py`). `ak_exams` uses it for survey/exam analysis (`survey_survey_ai.py`).

### Portal/Supplier Access

`ak_tender` exposes a supplier portal where vendors submit bids without Odoo accounts. Controllers in `ak_tender/controllers/` handle portal routes. Security rules in `ak_tender/security/` isolate portal users to their own tender lines only.

## Language Notes

- Business domain code, models, and views frequently use **Turkish** terminology: *ihale* (tender), *teklif* (offer/bid), *tedarikçi* (supplier), *satın alma* (purchasing), *onay* (approval).
- UI strings use `_()` for translation; Turkish translations live in `i18n/tr_TR.po` within each addon.
- Comments and documentation in custom addons are often in Turkish.

### Superset Analytics Integration (ak_superset_analytics)

`ak_superset_analytics` embeds Apache Superset dashboards in Odoo via JWT-based SSO. The `superset.dashboard` model stores per-dashboard configuration (URL, dashboard ID, JWT secret, Superset user credentials). Clicking a dashboard record opens it in a new browser tab via `view_dashboard_new_window()`, which generates a short-lived JWT and redirects to:

```
https://<superset_url>/superset/dashboard/<dashboard_id>/?jwt=<token>&standalone=2
```

**Production Superset instance**: `https://bilge.kardan.digital` — runs in **Docker** on VPS `145.223.116.76`

Currently configured dashboards in `od18`:

| Name | Dashboard ID | Purpose |
|---|---|---|
| Danone Exam Dashboard | 14 | Exam analytics for Danone |
| Abdi İbrahim Exam Dashboard | 15 | Exam analytics for Abdi İbrahim |

These dashboards read directly from the `od18` PostgreSQL database. The Superset `config.py` on `bilge.kardan.digital` must have a matching `JWT_SECRET_KEY` and a `CustomSSOSecurityManager` that validates the JWT. If dashboards show a Superset login page instead of content, the most common causes are: JWT secret mismatch, CORS misconfiguration, or the `CustomSSOSecurityManager` not being active on the Superset side.

Requires `PyJWT` in the Odoo venv:
```bash
/opt/odoo18-venv/bin/pip install PyJWT
```

## Infrastructure Notes

- **Database**: PostgreSQL, db name `od18`, user `odoo`
- **Workers**: 8 Gunicorn workers configured for ~205 concurrent users
- **Logging**: `ak_exams` logs at DEBUG level; general level is INFO
- **wkhtmltopdf**: at `/usr/local/bin/wkhtmltoimage` (used for PDF reports)
- **Proxy**: `proxy_mode = True` — runs behind a reverse proxy
- **Superset VPS**: `145.223.116.76` → `https://bilge.kardan.digital`, connects to `od18` PostgreSQL
