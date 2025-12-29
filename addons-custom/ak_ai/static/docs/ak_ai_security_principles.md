# KAI Security Principles - User Permission Model

## Core Security Principle

**KAI ALWAYS operates with the current user's permissions. NEVER bypasses security.**

```
🔒 GOLDEN RULE:
If a user cannot do something manually in Odoo,
KAI cannot automate it for them either.
```

## Permission Model

### How KAI Executes Actions

```python
# ❌ WRONG - Bypasses user permissions
records = env['sale.order'].sudo().search([...])

# ✅ CORRECT - Respects user permissions
records = env['sale.order'].search([...])  # Uses current user's rights
```

### Dynamic Permission Checks

**AI generates permission checks automatically based on the operation!**

#### Example 1: User wants to update prices

**User Request**: "ABC tedarikçisinin ürünlerinin fiyatlarını %10 artır"

**AI-Generated Code** (with automatic permission handling):
```python
# AI AUTOMATICALLY includes permission checks!

# Step 1: Check if user has access to product model
product_model = env['product.supplierinfo']

if not product_model.check_access_rights('write', raise_exception=False):
    result = {
        'success': False,
        'error': 'permission_denied',
        'message': 'Ürün fiyatlarını değiştirme yetkiniz bulunmamaktadır.',
        'suggestion': 'Satın alma müdürünüz ile iletişime geçin.'
    }
else:
    # Step 2: Find supplier (only if user has access)
    supplier = env['res.partner'].search([
        ('name', 'ilike', 'ABC'),
        ('supplier_rank', '>', 0)
    ], limit=1)
    
    if not supplier:
        result = {'success': False, 'message': 'ABC tedarikçisi bulunamadı'}
    else:
        # Step 3: Get and update products (with user's permissions)
        supplier_info = product_model.search([
            ('partner_id', '=', supplier.id)
        ])
        
        # User only sees records they have access to!
        # Record rules automatically applied
        
        try:
            updated = 0
            for info in supplier_info:
                old_price = info.price
                new_price = old_price * 1.10
                info.write({'price': new_price})  # Respects user permissions
                updated += 1
            
            result = {
                'success': True,
                'updated_count': updated,
                'message': f'{updated} ürün fiyatı güncellendi'
            }
        except AccessError as e:
            result = {
                'success': False,
                'error': 'access_denied',
                'message': 'Bazı ürünleri güncelleme yetkiniz yok: ' + str(e)
            }
```

**Key Points:**
- ✅ AI **automatically** adds permission checks
- ✅ Uses user's current environment (no sudo!)
- ✅ Handles AccessError gracefully
- ✅ Provides helpful error messages
- ✅ Suggests next steps if permission denied

#### Example 2: Create PR from list

**User Request**: "[15-item list] Buna göre PR oluştur"

**AI-Generated Code** (dynamic permission handling):
```python
# AI knows this operation requires 'create' permission

pr_model = env['purchase.requisition']

# Auto-generated permission check
if not pr_model.check_access_rights('create', raise_exception=False):
    result = {
        'success': False,
        'error': 'permission_denied',
        'message': 'Satın alma talebi oluşturma yetkiniz bulunmamaktadır.',
        'required_group': 'Satın Alma / Kullanıcı',
        'suggestion': 'Satın alma departmanı ile iletişime geçin.'
    }
else:
    # User has permission, proceed
    try:
        # Extract data...
        pr_data = {...}
        
        # Create PR (with user's permissions)
        pr = pr_model.create(pr_data)
        
        # Create lines (also checked by record rules)
        for line_data in lines:
            env['purchase.requisition.line'].create({
                'requisition_id': pr.id,
                ...
            })
        
        result = {
            'success': True,
            'pr_id': pr.id,
            'message': f'PR {pr.name} oluşturuldu'
        }
        
    except AccessError as e:
        result = {
            'success': False,
            'error': 'access_denied',
            'message': f'PR oluşturulamadı: {str(e)}'
        }
```

### How AI Knows What Permissions to Check

**AI Training Includes Odoo Permission Logic:**

```python
# AI learns from system prompt:
PERMISSION_GUIDANCE = """
Before any operation, analyze what permissions are needed:

Operation Type → Required Permission Check:
- search(), read() → check_access_rights('read')
- create() → check_access_rights('create')
- write(), update() → check_access_rights('write')
- unlink() → check_access_rights('unlink')

Always wrap operations in try/except AccessError.
Always provide helpful error messages in Turkish.
Never use sudo() to bypass permissions.
"""
```

### AI Dynamically Adjusts Based on Context

```python
# User Context (automatically provided to AI):
{
    "user": {
        "name": "Ahmet Yılmaz",
        "groups": ["Satın Alma / Kullanıcı", "Çalışan"],
        "is_admin": false
    },
    "permissions": {
        "purchase.requisition": {
            "read": true,
            "create": true,
            "write": false,  # Can't modify others' PRs
            "unlink": false
        }
    }
}

# AI uses this to generate appropriate code:
# - If user can't 'write', won't generate update code
# - If user can't 'create', informs them upfront
# - Always checks at runtime anyway (defense in depth)
```

## Forbidden Operations

### Strictly Prohibited

```python
# ❌ FORBIDDEN - Security bypass
env['model.name'].sudo()
env['model.name'].with_user(SUPERUSER_ID)

# ❌ FORBIDDEN - Direct database access
env.cr.execute("DELETE FROM ...")
env.cr.execute("UPDATE ...")

# ❌ FORBIDDEN - System operations
import os
os.system(...)
subprocess.call(...)

# ❌ FORBIDDEN - Dynamic code injection
eval(user_input)
exec(user_input)

# ❌ FORBIDDEN - File system access
open('/etc/passwd')
with open('file.txt', 'w') as f:
    f.write(...)
```

### Requires Explicit Confirmation

```python
# ⚠️ REQUIRES CONFIRMATION - Destructive operations
records.unlink()  # Delete
model.search([...]).write({'active': False})  # Mass update

# ⚠️ REQUIRES CONFIRMATION - Financial operations
invoice.action_post()  # Validate invoice
payment.action_post()  # Validate payment
```

## AI Code Generation Rules

### System Prompt Enforcement

```python
SECURITY_RULES = """
CRITICAL SECURITY RULES (NEVER VIOLATE):

1. ❌ NEVER use sudo() or with_user(SUPERUSER_ID)
2. ❌ NEVER access env.cr directly for write operations
3. ❌ NEVER use os, sys, subprocess modules
4. ❌ NEVER use eval() or exec() with user input
5. ❌ NEVER access file system (open, file, etc.)

6. ✅ ALWAYS use env (which has current user's rights)
7. ✅ ALWAYS check permissions before operations
8. ✅ ALWAYS handle AccessError gracefully
9. ✅ ALWAYS inform user if they lack permissions
10. ✅ ALWAYS log user attribution in audit trail

If an operation requires elevated permissions:
- Inform the user they don't have required access
- Suggest who they should contact (admin/manager)
- DO NOT attempt to bypass security
"""
```

### Permission-Aware Code Generation

```python
def generate_with_permission_checks(self, user_request):
    """Generate code that respects user permissions"""
    
    # Enhanced system prompt
    system_prompt = f"""{BASE_SYSTEM_PROMPT}

{SECURITY_RULES}

Current user: {self.env.user.name}
User groups: {', '.join(self.env.user.groups_id.mapped('name'))}

Generate code that:
1. Works within user's permissions
2. Checks access before operations
3. Handles permission errors gracefully
4. Informs user if operation is not allowed
"""
    
    # Generate code with security awareness
    code = self._call_ai(system_prompt, user_request)
    
    # Validate no security bypasses
    if 'sudo()' in code:
        raise SecurityError('Generated code attempts to bypass security!')
    
    return code
```

## Record Rules Respect

### Automatic Filtering

```python
# Record rules are AUTOMATICALLY applied
# User only sees their own records

# Example: Sales manager sees only their team's orders
env.user.groups_id  # ['group_sale_salesman']

# This automatically filters by record rules
orders = env['sale.order'].search([])
# Result: Only orders where user_id = current_user OR team_id = user's team
```

### Field-Level Security

```python
# Some fields may be readonly for certain users
order = env['sale.order'].browse(order_id)

try:
    order.write({'state': 'sale'})
except AccessError as e:
    return {
        'success': False,
        'error': 'Field access denied',
        'message': 'Bu alanı değiştirme yetkiniz yok'
    }
```

## User Attribution & Audit

### Every Action is Attributed

```python
# All actions logged with user info
log_entry = {
    'user_id': env.user.id,
    'user_name': env.user.name,
    'action': 'create_purchase_requisition',
    'timestamp': fields.Datetime.now(),
    'success': True,
    'details': {
        'pr_id': pr.id,
        'line_count': len(pr.line_ids)
    }
}

env['ak_ai.code.execution.log'].create(log_entry)
```

### Audit Trail

```python
class AkAiCodeExecutionLog(models.Model):
    _name = 'ak_ai.code.execution.log'
    
    user_id = fields.Many2one('res.users', 'User', required=True)
    # User who requested the action - NOT KAI bot user
    
    code = fields.Text('Executed Code')
    result = fields.Text('Result')
    success = fields.Boolean('Success')
    timestamp = fields.Datetime('Timestamp', default=fields.Datetime.now)
    
    # What was accessed/modified
    affected_records = fields.Char('Affected Records')
    operation_type = fields.Selection([
        ('read', 'Read'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete')
    ])
```

## Permission Error Handling

### Graceful Failures

```python
def execute_with_permission_handling(self, code, context):
    """Execute with proper permission error handling"""
    
    try:
        result = self._execute_code(code, context)
        return result
        
    except AccessError as e:
        # User doesn't have permission
        return {
            'success': False,
            'error_type': 'permission_denied',
            'error': str(e),
            'message': 'Bu işlem için yetkiniz bulunmamaktadır.',
            'suggestion': 'Lütfen sistem yöneticiniz ile iletişime geçin.',
            'required_groups': self._extract_required_groups(e)
        }
    
    except ValidationError as e:
        # Business logic validation failed
        return {
            'success': False,
            'error_type': 'validation_error',
            'error': str(e),
            'message': 'İşlem doğrulanamadı: ' + str(e)
        }
        
    except Exception as e:
        # Other errors
        _logger.error(f"Execution error: {e}")
        return {
            'success': False,
            'error_type': 'execution_error',
            'error': str(e),
            'message': 'İşlem sırasında bir hata oluştu.'
        }
```

### Informative Error Messages

```python
# When user lacks permissions
if not has_permission:
    return {
        'success': False,
        'message': """
❌ Yetki Hatası

Bu işlemi gerçekleştirmek için gerekli yetkiye sahip değilsiniz.

📋 Gereken Yetki:
   • {required_group_name}

👤 Mevcut Yetki Seviyeniz:
   • {current_user_groups}

💡 Öneri:
   Bu işlem için sistem yöneticiniz veya {admin_role} ile iletişime geçin.
""",
        'contact_admin': True,
        'required_access': required_group_name
    }
```

## Multi-Company Security

### Company-Specific Data

```python
# KAI respects multi-company rules
current_company = env.company

# User can only access data from their company/companies
allowed_companies = env.user.company_ids

# Records automatically filtered by company
partners = env['res.partner'].search([])
# Only partners accessible to user's companies
```

## External User Restrictions

### Portal Users

```python
# Portal users have very limited access
if env.user.has_group('base.group_portal'):
    # KAI provides limited functionality
    # - View own records only
    # - No create/update/delete
    # - Read-only information
    
    return {
        'message': 'Portal kullanıcıları bu işlemi gerçekleştiremez.',
        'allowed_operations': ['view_own_orders', 'download_invoices']
    }
```

## Summary: Security Guarantees

### What KAI WILL Do:
- ✅ Execute with current user's permissions
- ✅ Respect all record rules
- ✅ Check field-level security
- ✅ Honor multi-company rules
- ✅ Log all actions with user attribution
- ✅ Handle permission errors gracefully
- ✅ Inform users about access restrictions

### What KAI WILL NEVER Do:
- ❌ Use sudo() to bypass permissions
- ❌ Access restricted records
- ❌ Modify read-only fields
- ❌ Execute system commands
- ❌ Access file system
- ❌ Perform operations user can't do manually

### Trust Model:

```
KAI is a productivity tool, NOT a security bypass tool.

KAI = User + AI Assistance
KAI ≠ User + Super User Powers

If User can't → KAI can't
If User can → KAI makes it easier
```

## Compliance

This security model ensures:
- ✅ **SOC 2 Compliance**: User-level attribution
- ✅ **GDPR Compliance**: No unauthorized data access
- ✅ **Audit Requirements**: Complete action trail
- ✅ **SOX Compliance**: Segregation of duties maintained
- ✅ **Internal Controls**: Existing controls not bypassed

---

**Remember**: KAI is a smart assistant, not a magic wand. It helps users work faster within their existing permissions, but never bypasses Odoo's security model.
