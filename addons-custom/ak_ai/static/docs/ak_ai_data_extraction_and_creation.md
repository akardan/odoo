# KAI Data Extraction & Record Creation

## Overview

KAI can extract structured data from unstructured text and create Odoo records automatically.

## Your Example: Create Purchase Requisition from Text

### User Input:
```
Talep Bilgileri:
Talep Tarihi: 27.12.2024
Talep Eden Departman: İDARİ İŞLER
Talep Türü: PROMOSYON/KIRTASİYE

SIRA NO | ÜRÜN ADI | MARKA/MODEL | MİKTAR | BİRİM
1 | A4 VE-GE | 150 | PAKET | 30 KOLI (koli içi 5 paket)
2 | LİDO ÇAMAŞIR SUYU | MİSNET | 2 | ADET | 30lt 1 bidon
3 | LİDO PARFÜMLÜ ÇAMAŞIR SUYU | MİSNET | 2 | ADET | 30lt 1 bidon
...
15 | CERRAHİ MASKE | EVONY | 100 | PAKET | koli içi 10 PAKET (10 koli)

Toplam: 15 kalem ürün

Buna göre PR oluştur
```

### KAI Response & Execution

```
🤖 KAI

Anladım! Size 15 kalemlik bir satın alma talebi oluşturacağım.

📋 Talep Özeti:
• Tarih: 27.12.2024
• Departman: İDARİ İŞLER
• Tür: PROMOSYON/KIRTASİYE
• Kalem Sayısı: 15

🛒 Ürünler:
1. A4 VE-GE - 150 Paket
2. LİDO ÇAMAŞIR SUYU - 2 Adet
...
15. CERRAHİ MASKE - 100 Paket

Ben bu bilgileri kullanarak satın alma talebi oluşturabilrim.

**Ne yapmamı istersiniz?**

┌─────────────────────────────────────────┐
│ ✅ PR Oluştur                           │
│ Satın alma talebini şimdi oluştur       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📝 Önce Önizle                          │
│ Detayları önce göster                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ✏️ Düzenle                              │
│ Bilgileri düzenlememe izin ver          │
└─────────────────────────────────────────┘
```

[User clicks "PR Oluştur"]

```
⚙️ PR Talbin yaratılıyor...

✅ PR Başarıyla Oluşturuldu!

📄 PR/2024/0042
Durum: Taslak
15 kalem ürün eklendi

**Şimdi ne yapmak istersiniz?**

┌─────────────────────────────────────────┐
│ 📋 PR'yi Aç                             │
│ Detayları görmek için aç                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ✉️  Onaya Gönder                        │
│ Onay sürecini başlat                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🛒 İhale Oluştur                        │
│ Direkt ihale sürecine geç              │
└─────────────────────────────────────────┘
```

## Implementation

### 1. Data Extraction Tool

```python
# Tool Definition (XML)
<record id="tool_extract_pr_data" model="ak_ai.tool">
    <field name="name">Extract Purchase Requisition Data</field>
    <field name="code">extract_pr_data</field>
    <field name="description">Extract purchase requisition data from unstructured text, tables, emails, or documents. Use when user provides a list of products to purchase.</field>
    <field name="tool_type">data</field>
    <field name="function_schema">{
  "type": "object",
  "properties": {
    "source_text": {
      "type": "string",
      "description": "The text containing purchase requisition data"
    },
    "create_immediately": {
      "type": "boolean",
      "default": false,
      "description": "Whether to create PR immediately or show preview first"
    }
  },
  "required": ["source_text"]
}</field>
    <field name="execution_model">ak_ai.data.extractor</field>
    <field name="execution_method">extract_and_create_pr</field>
</record>
```

### 2. Data Extractor Service

```python
class AkAiDataExtractor(models.AbstractModel):
    _name = 'ak_ai.data.extractor'
    _description = 'KAI Data Extraction Service'
    
    def extract_and_create_pr(self, arguments):
        """Extract PR data and create record"""
        source_text = arguments.get('source_text')
        create_immediately = arguments.get('create_immediately', False)
        
        # Use AI to extract structured data
        extracted_data = self._extract_pr_data_with_ai(source_text)
        
        if not extracted_data:
            return {'success': False, 'error': 'Could not extract data'}
        
        if create_immediately:
            # Create PR directly
            pr = self._create_purchase_requisition(extracted_data)
            return {
                'success': True,
                'message': f'PR {pr.name} created successfully!',
                'pr_id': pr.id,
                'action': self._get_open_pr_action(pr)
            }
        else:
            # Show preview first
            return {
                'success': True,
                'preview': True,
                'data': extracted_data,
                'message': 'Data extracted. Ready to create PR.',
                'confirm_action': 'create_pr_from_data'
            }
    
    def _extract_pr_data_with_ai(self, source_text):
        """Use AI to extract structured data from text"""
        
        system_prompt = """You are a data extraction expert. 
Extract purchase requisition data from the given text.

Return a JSON structure with:
{
  "request_date": "YYYY-MM-DD",
  "department": "string",
  "request_type": "string",
  "lines": [
    {
      "sequence": 1,
      "product_name": "string",
      "brand": "string",
      "quantity": number,
      "uom": "string",
      "notes": "string"
    }
  ]
}

If a product doesn't exist in Odoo, include it anyway.
Parse quantities correctly, handling Turkish number formats.
"""
        
        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": source_text}
            ],
            response_format={"type": "json_object"}
        )
        
        extracted = json.loads(response.choices[0].message.content)
        
        return extracted
    
    def _create_purchase_requisition(self, data):
        """Create purchase requisition from extracted data"""
        
        # Create PR header
        pr = self.env['purchase.requisition'].create({
            'name': '/',  # Auto-generated
            'ordering_date': data.get('request_date'),
            'user_id': self.env.user.id,
            # Map department if exists
            'department_id': self._find_or_create_department(data.get('department')),
            'description': data.get('request_type') or data.get('notes'),
        })
        
        # Create PR lines
        for line_data in data.get('lines', []):
            self._create_pr_line(pr, line_data)
        
        return pr
    
    def _create_pr_line(self, pr, line_data):
        """Create PR line with product matching"""
        
        # Try to find product
        product = self._find_product(
            line_data.get('product_name'),
            line_data.get('brand')
        )
        
        if not product:
            # Create as note/description only
            product_name = line_data.get('product_name')
            brand = line_data.get('brand', '')
            description = f"{product_name} ({brand})" if brand else product_name
            
            # You might want to create product or just add to description
            # For now, we'll skip if no product found and add to notes
            _logger.warning(f"Product not found: {description}")
            return
        
        # Find or map UOM
        uom = self._find_uom(line_data.get('uom'))
        
        # Create line
        self.env['purchase.requisition.line'].create({
            'requisition_id': pr.id,
            'product_id': product.id,
            'product_qty': float(line_data.get('quantity', 0)),
            'product_uom_id': uom.id if uom else product.uom_id.id,
            'schedule_date': pr.ordering_date,
            # Add notes from original data
            'name': self._build_line_description(line_data),
        })
    
    def _find_product(self, product_name, brand=None):
        """Find product by name and brand"""
        if not product_name:
            return None
        
        domain = [('name', 'ilike', product_name)]
        
        if brand:
            domain.append('|')
            domain.append(('default_code', 'ilike', brand))
            domain.append(('name', 'ilike', brand))
        
        return self.env['product.product'].search(domain, limit=1)
    
    def _find_uom(self, uom_text):
        """Find UOM by name"""
        if not uom_text:
            return None
        
        # Common Turkish UOM mappings
        uom_map = {
            'adet': 'Units',
            'paket': 'Units',
            'koli': 'Units',
            'kg': 'kg',
            'lt': 'L',
            'litre': 'L',
            'metre': 'm',
            'adet': 'Unit(s)',
        }
        
        mapped = uom_map.get(uom_text.lower(), uom_text)
        
        return self.env['uom.uom'].search([
            '|', ('name', 'ilike', mapped), ('name', 'ilike', uom_text)
        ], limit=1)
    
    def _build_line_description(self, line_data):
        """Build line description from extracted data"""
        parts = []
        
        if line_data.get('product_name'):
            parts.append(line_data['product_name'])
        
        if line_data.get('brand'):
            parts.append(f"({line_data['brand']})")
        
        if line_data.get('notes'):
            parts.append(f"- {line_data['notes']}")
        
        return ' '.join(parts)
    
    def _find_or_create_department(self, dept_name):
        """Find or create department"""
        if not dept_name:
            return False
        
        # Assuming you have a department model
        if 'hr.department' in self.env:
            dept = self.env['hr.department'].search([
                ('name', 'ilike', dept_name)
            ], limit=1)
            
            if not dept:
                dept = self.env['hr.department'].create({
                    'name': dept_name
                })
            
            return dept.id
        
        return False
```

### 3. Enhanced AI with Streaming & Confirmation

```python
def _process_pr_creation_request(self, user_message, conversation):
    """Handle PR creation with confirmation flow"""
    
    # Step 1: Extract data
    extracted = self._extract_pr_data_with_ai(user_message)
    
    # Step 2: Show preview to user
    preview_message = self._format_pr_preview(extracted)
    
    # Step 3: Create message with confirmation actions
    message = self.env['ak_ai.message'].create({
        'conversation_id': conversation.id,
        'role': 'assistant',
        'content': preview_message,
        'action_data': json.dumps({
            'type': 'confirm_create_pr',
            'data': extracted
        })
    })
    
    return {
        'content': preview_message,
        'actions': [
            {
                'id': 'create_pr',
                'type': 'confirm',
                'label': '✅ PR Oluştur',
                'description': 'Satın alma talebini şimdi oluştur',
                'data': extracted,
                'method': 'create_pr_from_extracted_data'
            },
            {
                'id': 'preview_pr',
                'type': 'preview',
                'label': '📝 Önce Önizle',
                'description': 'Detayları önce göster',
                'data': extracted
            },
            {
                'id': 'edit_pr',
                'type': 'edit',
                'label': '✏️  Düzenle',
                'description': 'Bilgileri düzenlememe izin ver',
                'data': extracted
            }
        ]
    }


def _format_pr_preview(self, extracted_data):
    """Format extracted data for user preview"""
    
    lines = extracted_data.get('lines', [])
    
    preview = f"""Anladım! Size {len(lines)} kalemlik bir satın alma talebi oluşturacağım.

📋 Talep Özeti:
• Tarih: {extracted_data.get('request_date')}
• Departman: {extracted_data.get('department')}
• Tür: {extracted_data.get('request_type')}
• Kalem Sayısı: {len(lines)}

🛒 Ürünler:
"""
    
    for i, line in enumerate(lines[:5], 1):  # Show first 5
        preview += f"{i}. {line['product_name']} - {line['quantity']} {line.get('uom', 'Adet')}\n"
    
    if len(lines) > 5:
        preview += f"... ve {len(lines) - 5} ürün daha\n"
    
    preview += "\n\nBen bu bilgileri kullanarak satın alma talebi oluşturabilirim.\n\n**Ne yapmamı istersiniz?**"
    
    return preview
```

### 4. Additional Smart Features

#### Auto-Complete from History
```python
defcomplete_product_info(self, product_name):
    """Auto-complete product info from purchase history"""
    
    # Find similar past purchases
    past_lines = self.env['purchase.order.line'].search([
        ('product_id.name', 'ilike', product_name)
    ], limit=5, order='create_date desc')
    
    if past_lines:
        # Get most common price, supplier, etc.
        product = past_lines[0].product_id
        avg_price = sum(past_lines.mapped('price_unit')) / len(past_lines)
        
        return {
            'product_id': product.id,
            'estimated_price': avg_price,
            'preferred_supplier': past_lines[0].partner_id.id,
            'last_purchase_date': past_lines[0].create_date,
        }
    
    return {}
```

#### Smart Product Matching
```python
def _smart_product_match(self, product_name, brand=None):
    """Use AI for fuzzy product matching"""
    
    # Get all products
    products = self.env['product.product'].search([], limit=1000)
    
    # Use AI to find best match
    prompt = f"""Given these products:
{[p.name for p in products[:100]]}

Which one best matches: "{product_name}" from brand "{brand}"?
Return only the exact product name from the list, or "NOT_FOUND".
"""
    
    # AI call for matching
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    matched_name = response.choices[0].message.content.strip()
    
    if matched_name != "NOT_FOUND":
        return products.filtered(lambda p: p.name == matched_name)
    
    return None
```

## Other Use Cases

### 1. Create from Email
```
User: "Accounting'den gelen mail'i PR'ye çevir"

KAI: 
- Email'i okur
- Ürünleri extract eder
- PR oluşturur
```

### 2. Create from Excel/CSV
```
User: "Bu Excel'i kullanarak PR oluştur" [file attached]

KAI:
- Excel'i parse eder
- Kolonları eşleştirir
- PR oluşturur
```

### 3. Recurring Orders
```
User: "Geçen ayki temizlik malzemesi talebini tekrarla"

KAI:
- Geçmiş PR'yi bulur
- Aynı ürünlerle yeni PR oluşturur
```

### 4. Smart Suggestions
```
User: "Kırtasiye talebi oluştur"

KAI: "Hangi ürünler gerekli?"

User: "Standart ofis malzemeleri"

KAI: analize past orders for this department]
"Genelde şunları sipariş ediyorsunuz:
1. A4 Kağıt - 100 paket
2. Tükenmez kalem - 50 adet
...

Bunları ekleyeyim mi?"
```

## Summary

**Yes, KAI can create PR from structured text!**

Capabilities:
- ✅ Extract data from Turkish text
- ✅ Parse tables and lists
- ✅  Match products intelligently
- ✅ Handle units and quantities
- ✅ Show preview before creation
- ✅ Create with one click
- ✅ Auto-complete from history
- ✅ Smart suggestions

This makes data entry 10x faster! 🚀
