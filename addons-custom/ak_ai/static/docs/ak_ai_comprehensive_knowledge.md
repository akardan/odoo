# KAI Comprehensive Knowledge Builder - Complete Implementation

## Complete Knowledge Builder Implementation

```python
class AkAiKnowledgeBuilder(models.Model):
    _name = 'ak_ai.knowledge.builder'
    _description = 'KAI Comprehensive Knowledge Builder'
    
    def build_odoo_knowledge(self):
        """Build comprehensive knowledge from Odoo metadata"""
        knowledge = {
            # Core Structure
            'models': self._learn_models(),
            'fields': self._learn_fields(),
            'views': self._learn_views(),
            'workflows': self._learn_workflows(),
            'menus': self._learn_menus(),
            
            # Security & Access
            'users': self._learn_users(),
            'groups': self._learn_groups(),
            'permissions': self._learn_permissions(),
            'record_rules': self._learn_record_rules(),
            
            # Organization
            'companies': self._learn_companies(),
            'teams': self._learn_teams(),
            'departments': self._learn_departments(),
            
            # Configuration
            'settings': self._learn_settings(),
            'parameters': self._learn_system_parameters(),
            
            # Business Data
            'partners': self._learn_partners(),
            'products': self._learn_products(),
            'currencies': self._learn_currencies(),
            # Integrations
            'external_apis': self._learn_external_apis(),
            'webhooks': self._learn_webhooks(),
            'cron_jobs': self._learn_cron_jobs(),
            
            # Custom Modules
            'installed_modules': self._learn_installed_modules(),
            'custom_modules': self._learn_custom_modules(),
        }
        
        # Cache knowledge for faster access
        self._cache_knowledge(knowledge)
        
        return knowledge
    
    # ===== CORE STRUCTURE =====
    
    def _learn_models(self):
        """Learn about all models in the system"""
        models_info = {}
        
        for model_name in self.env.registry.models():
            try:
                model = self.env[model_name]
                
                if model_name.startswith('_'):
                    continue
                
                models_info[model_name] = {
                    'name': model_name,
                    'description': model._description,
                    'table': model._table if hasattr(model, '_table') else None,
                    'fields count': len(model._fields),
                    'inherits': model._inherits if hasattr(model, '_inherits') else {},
                    'is_transient': model._transient,
                    'can_create': model.check_access_rights('create', raise_exception=False),
                    'can_read': model.check_access_rights('read', raise_exception=False),
                }
            except:
                continue
        
        return models_info
    
    def _learn_fields(self):
        """Learn about fields and their purposes"""
        field_info = {}
        
        important_models = [
            'res.partner', 'res.users', 'sale.order', 'purchase.order',
            'account.move', 'stock.picking', 'product.product', 
            'crm.lead', 'project.project', 'hr.employee'
        ]
        
        for model_name in important_models:
            try:
                if model_name not in self.env:
                    continue
                    
                model = self.env[model_name]
                field_info[model_name] = {}
                
                for fname, field in model._fields.items():
                    if fname.startswith('_'):
                        continue
                    
                    field_info[model_name][fname] = {
                        'name': fname,
                        'type': field.type,
                        'string': field.string,
                        'help': field.help or '',
                        'required': field.required,
                        'readonly': field.readonly,
                        'compute': bool(field.compute),
                        'store': field.store,
                    }
            except:
                continue
        
        return field_info
    
    def _learn_views(self):
        """Learn about views"""
        views_info = {}
        
        views = self.env['ir.ui.view'].search([
            ('type', 'in', ['form', 'tree', 'kanban', 'calendar'])
        ])
        
        for view in views:
            model_name = view.model
            if model_name not in views_info:
                views_info[model_name] = []
            
            views_info[model_name].append({
                'id': view.id,
                'name': view.name,
                'type': view.type,
                'priority': view.priority,
            })
        
        return views_info
    
    def _learn_workflows(self):
        """Learn state transitions and workflows"""
        workflows = {}
        
        for model_name in self.env.registry.models():
            try:
                model = self.env[model_name]
                if 'state' in model._fields:
                    field = model._fields['state']
                    if field.type == 'selection':
                        workflows[model_name] = {
                            'states': dict(field.selection).keys() if callable(field.selection) else dict(field.selection),
                            'default': field.default,
                            'has_state_field': True
                        }
            except:
                continue
        
        return workflows
    
    def _learn_menus(self):
        """Learn about menu structure"""
        menus_info = {}
        
        menus = self.env['ir.ui.menu'].search([])
        
        for menu in menus:
            menus_info[menu.id] = {
                'name': menu.name,
                'parent': menu.parent_id.name if menu.parent_id else None,
                'action': menu.action.name if menu.action else None,
                'sequence': menu.sequence,
            }
        
        return menus_info
    
    # ===== SECURITY & ACCESS =====
    
    def _learn_users(self):
        """Learn about users (without sensitive data)"""
        users_info = {}
        
        users = self.env['res.users'].search([('active', '=', True)])
        
        for user in users:
            users_info[user.id] = {
                'id': user.id,
                'name': user.name,
                'login': user.login,  # Not shown to KAI, just for internal mapping
                'lang': user.lang,
                'tz': user.tz,
                'company': user.company_id.name,
                'companies': [c.name for c in user.company_ids],
                'groups': [g.name for g in user.groups_id],
                'is_admin': user.has_group('base.group_system'),
                'is_internal': not user.share,
            }
        
        return users_info
    
    def _learn_groups(self):
        """Learn about security groups"""
        groups_info = {}
        
        groups = self.env['res.groups'].search([])
        
        for group in groups:
            groups_info[group.id] = {
                'name': group.name,
                'category': group.category_id.name if group.category_id else None,
                'comment': group.comment or '',
                'users_count': len(group.users),
                'implied_groups': [g.name for g in group.implied_ids],
            }
        
        return groups_info
    
    def _learn_permissions(self):
        """Learn about model access rights"""
        permissions_info = {}
        
        access_rights = self.env['ir.model.access'].search([])
        
        for access in access_rights:
            model_name = access.model_id.model
            if model_name not in permissions_info:
                permissions_info[model_name] = []
            
            permissions_info[model_name].append({
                'group': access.group_id.name if access.group_id else 'All Users',
                'read': access.perm_read,
                'write': access.perm_write,
                'create': access.perm_create,
                'unlink': access.perm_unlink,
            })
        
        return permissions_info
    
    def _learn_record_rules(self):
        """Learn about record-level security rules"""
        rules_info = {}
        
        rules = self.env['ir.rule'].search([('active', '=', True)])
        
        for rule in rules:
            model_name = rule.model_id.model
            if model_name not in rules_info:
                rules_info[model_name] = []
            
            rules_info[model_name].append({
                'name': rule.name,
                'groups': [g.name for g in rule.groups],
                'domain': rule.domain_force,
                'permissions': {
                    'read': rule.perm_read,
                    'write': rule.perm_write,
                    'create': rule.perm_create,
                    'unlink': rule.perm_unlink,
                }
            })
        
        return rules_info
    
    # ===== ORGANIZATION =====
    
    def _learn_companies(self):
        """Learn about companies in the system"""
        companies_info = {}
        
        companies = self.env['res.company'].search([])
        
        for company in companies:
            companies_info[company.id] = {
                'name': company.name,
                'currency': company.currency_id.name,
                'country': company.country_id.name if company.country_id else None,
                'vat': company.vat,
                'employees_count': len(company.user_ids),
            }
        
        return companies_info
    
    def _learn_teams(self):
        """Learn about sales/CRM teams"""
        teams_info = {}
        
        if 'crm.team' in self.env:
            teams = self.env['crm.team'].search([])
            
            for team in teams:
                teams_info[team.id] = {
                    'name': team.name,
                    'members': [m.name for m in team.member_ids],
                    'alias': team.alias_name,
                }
        
        return teams_info
    
    def _learn_departments(self):
        """Learn about HR departments"""
        departments_info = {}
        
        if 'hr.department' in self.env:
            departments = self.env['hr.department'].search([])
            
            for dept in departments:
                departments_info[dept.id] = {
                    'name': dept.name,
                    'manager': dept.manager_id.name if dept.manager_id else None,
                    'parent': dept.parent_id.name if dept.parent_id else None,
                }
        
        return departments_info
    
    # ===== CONFIGURATION =====
    
    def _learn_settings(self):
        """Learn about system settings"""
        settings_info = {}
        
        # Get config settings models
        config_models = [
            model for model in self.env.registry.models()
            if 'res.config.settings' in model
        ]
        
        for model_name in config_models:
            try:
                model = self.env[model_name]
                settings_info[model_name] = {
                    'description': model._description,
                    'fields': list(model._fields.keys())
                }
            except:
                continue
        
        return settings_info
    
    def _learn_system_parameters(self):
        """Learn about system parameters"""
        params_info = {}
        
        params = self.env['ir.config_parameter'].search([])
        
        for param in params:
            # Don't expose sensitive parameters
            if any(sensitive in param.key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                params_info[param.key] = {'value': '***REDACTED***'}
            else:
                params_info[param.key] = {'value': param.value}
        
        return params_info
    
    # ===== BUSINESS DATA =====
    
    def _learn_partners(self):
        """Learn about partner types and categories"""
        partners_info = {
            'total_count': self.env['res.partner'].search_count([]),
            'customer_count': self.env['res.partner'].search_count([('customer_rank', '>', 0)]),
            'supplier_count': self.env['res.partner'].search_count([('supplier_rank', '>', 0)]),
            'categories': []
        }
        
        if 'res.partner.category' in self.env:
            categories = self.env['res.partner.category'].search([])
            partners_info['categories'] = [
                {'name': cat.name, 'color': cat.color}
                for cat in categories
            ]
        
        return partners_info
    
    def _learn_products(self):
        """Learn about product types and categories"""
        products_info = {}
        
        if 'product.product' in self.env:
            products_info = {
                'total_count': self.env['product.product'].search_count([]),
                'categories': [],
                'types': {}
            }
            
            # Categories
            if 'product.category' in self.env:
                categories = self.env['product.category'].search([])
                products_info['categories'] = [
                    {'name': cat.name, 'parent': cat.parent_id.name if cat.parent_id else None}
                    for cat in categories
                ]
            
            # Types distribution
            for ptype in ['product', 'consu', 'service']:
                count = self.env['product.product'].search_count([('type', '=', ptype)])
                products_info['types'][ptype] = count
        
        return products_info
    
    def _learn_currencies(self):
        """Learn about active currencies"""
        currencies_info = {}
        
        currencies = self.env['res.currency'].search([('active', '=', True)])
        
        for currency in currencies:
            currencies_info[currency.name] = {
                'name': currency.name,
                'symbol': currency.symbol,
                'rate': currency.rate,
                'position': currency.position,
            }
        
        return currencies_info
    
    def _learn_languages(self):
        """Learn about installed languages"""
        languages_info = {}
        
        languages = self.env['res.lang'].search([])
        
        for lang in languages:
            languages_info[lang.code] = {
                'name': lang.name,
                'code': lang.code,
                'iso_code': lang.iso_code,
                'direction': lang.direction,
            }
        
        return languages_info
    
    # ===== INTEGRATIONS =====
    
    def _learn_external_apis(self):
        """Learn about external API configurations"""
        apis_info = {}
        
        # This would depend on your custom integrations
        # Example: payment providers, shipping carriers, etc.
        
        if 'payment.provider' in self.env:
            providers = self.env['payment.provider'].search([])
            apis_info['payment_providers'] = [
                {'name': p.name, 'code': p.code, 'state': p.state}
                for p in providers
            ]
        
        if 'delivery.carrier' in self.env:
            carriers = self.env['delivery.carrier'].search([])
            apis_info['delivery_carriers'] = [
                {'name': c.name, 'provider': c.delivery_type}
                for c in carriers
            ]
        
        return apis_info
    
    def _learn_webhooks(self):
        """Learn about webhooks"""
        webhooks_info = {}
        
        if 'webhook' in self.env:
            webhooks = self.env['webhook'].search([])
            for webhook in webhooks:
                webhooks_info[webhook.id] = {
                    'name': webhook.name,
                    'url': webhook.url,
                    'model': webhook.model_id.model,
                }
        
        return webhooks_info
    
    def _learn_cron_jobs(self):
        """Learn about scheduled actions"""
        cron_info = {}
        
        crons = self.env['ir.cron'].search([('active', '=', True)])
        
        for cron in crons:
            cron_info[cron.id] = {
                'name': cron.name,
                'model': cron.model_id.model if cron.model_id else None,
                'function': cron.code,
                'interval': f"{cron.interval_number} {cron.interval_type}",
                'next_run': str(cron.nextcall) if cron.nextcall else None,
            }
        
        return cron_info
    
    # ===== CUSTOM MODULES =====
    
    def _learn_installed_modules(self):
        """Learn about installed modules"""
        modules_info = {}
        
        modules = self.env['ir.module.module'].search([
            ('state', '=', 'installed')
        ])
        
        for module in modules:
            modules_info[module.name] = {
                'name': module.name,
                'display_name': module.shortdesc,
                'summary': module.summary,
                'author': module.author,
                'category': module.category_id.name if module.category_id else None,
                'version': module.latest_version,
            }
        
        return modules_info
    
    def _learn_custom_modules(self):
        """Identify custom/non-standard modules"""
        custom_modules = {}
        
        modules = self.env['ir.module.module'].search([
            ('state', '=', 'installed'),
            ('author', 'not ilike', 'Odoo')
        ])
        
        for module in modules:
            custom_modules[module.name] = {
                'name': module.name,
                'author': module.author,
                'description': module.description,
            }
        
        return custom_modules
    
    # ===== CACHING =====
    
    def _cache_knowledge(self, knowledge):
        """Cache knowledge for faster access"""
        cache_record = self.env['ak_ai.knowledge.cache'].search([], limit=1)
        
        if not cache_record:
            cache_record = self.env['ak_ai.knowledge.cache'].create({
                'name': 'System Knowledge Cache',
                'knowledge_data': json.dumps(knowledge),
                'last_updated': fields.Datetime.now()
            })
        else:
            cache_record.write({
                'knowledge_data': json.dumps(knowledge),
                'last_updated': fields.Datetime.now()
            })
    
    def get_cached_knowledge(self):
        """Get cached knowledge"""
        cache = self.env['ak_ai.knowledge.cache'].search([], limit=1)
        
        if cache:
            # Check if cache is fresh (less than 24 hours old)
            age = fields.Datetime.now() - cache.last_updated
            if age.total_seconds() < 86400:  # 24 hours
                return json.loads(cache.knowledge_data)
        
        # Cache is old or doesn't exist, rebuild
        return self.build_odoo_knowledge()
    
    # ===== QUERY METHODS =====
    
    def query_knowledge(self, query_type, filters=None):
        """Query specific knowledge"""
        knowledge = self.get_cached_knowledge()
        
        if query_type in knowledge:
            data = knowledge[query_type]
            
            # Apply filters if provided
            if filters:
                # Simple filtering logic
                return self._filter_data(data, filters)
            
            return data
        
        return {}
    
    def _filter_data(self, data, filters):
        """Filter data based on criteria"""
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if all(filter_func(key, value) for filter_func in filters):
                    filtered[key] = value
            return filtered
        return data


# Cache Model
class AkAiKnowledgeCache(models.Model):
    _name = 'ak_ai.knowledge.cache'
    _description = 'KAI Knowledge Cache'
    
    name = fields.Char('Name', default='System Knowledge')
    knowledge_data = fields.Text('Knowledge Data (JSON)', required=True)
    last_updated = fields.Datetime('Last Updated', default=fields.Datetime.now)
    
    @api.model
    def _cron_refresh_knowledge(self):
        """Scheduled job to refresh knowledge daily"""
        builder = self.env['ak_ai.knowledge.builder']
        knowledge = builder.build_odoo_knowledge()
        _logger.info(f"KAI Knowledge refreshed: {len(knowledge)} categories")
```

## Usage in AI Service

```python
class AkAiService(models.AbstractModel):
    _inherit = 'ak_ai.service'
    
    def _build_system_prompt_with_knowledge(self, conversation):
        """Build system prompt with relevant knowledge"""
        
        base_prompt = """You are KAI (Kardan AI), an intelligent assistant for Odoo ERP system.

You have access to comprehensive knowledge about this Odoo instance.
"""
        
        # Get knowledge builder
        knowledge_builder = self.env['ak_ai.knowledge.builder']
        
        # Get relevant knowledge based on context
        if conversation.context_mode == 'record' and conversation.context_model:
            # Model-specific knowledge
            model_knowledge = {
                'model_info': knowledge_builder.query_knowledge('models', 
                    filters=[lambda k, v: k == conversation.context_model]),
                'fields': knowledge_builder.query_knowledge('fields',
                    filters=[lambda k, v: k == conversation.context_model]),
                'permissions': knowledge_builder.query_knowledge('permissions',
                    filters=[lambda k, v: k == conversation.context_model]),
            }
            
            base_prompt += f"\n\nContext: You are helping with {conversation.context_model}\n"
            base_prompt += f"Available fields: {', '.join(model_knowledge['fields'].get(conversation.context_model, {}).keys())}\n"
        
        # User-specific knowledge
        user_knowledge = knowledge_builder.query_knowledge('users',
            filters=[lambda k, v: k == self.env.user.id])
        
        if user_knowledge:
            user_info = list(user_knowledge.values())[0]
            base_prompt += f"\n\nCurrent user: {user_info['name']}"
            base_prompt += f"\nUser language: {user_info['lang']}"
            base_prompt += f"\nUser groups: {', '.join(user_info['groups'])}"
        
        # Company knowledge
        company_knowledge = knowledge_builder.query_knowledge('companies',
            filters=[lambda k, v: k == self.env.company.id])
        
        if company_knowledge:
            company_info = list(company_knowledge.values())[0]
            base_prompt += f"\n\nCompany: {company_info['name']}"
            base_prompt += f"\nCurrency: {company_info['currency']}"
        
        return base_prompt
```

This comprehensive knowledge builder ensures KAI knows about:
- ✅ All models, fields, and views
- ✅ Users, groups, and permissions
- ✅ Companies, teams, and departments  
- ✅ System settings and parameters
- ✅ Business data (partners, products)
- ✅ Integrations and APIs
- ✅ Installed and custom modules
- ✅ Workflows and state machines
- ✅ Cron jobs and automations

KAI will have complete awareness of your Odoo system!
