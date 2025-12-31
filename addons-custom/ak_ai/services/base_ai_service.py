# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError, AccessError
import logging
import json

_logger = logging.getLogger(__name__)


class AkAiService(models.AbstractModel):
    """Base AI Service - Security-First Architecture"""
    _name = 'ak_ai.service'
    _description = 'Base AI Service'

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

    @api.model
    def get_service(self):
        """Get the appropriate AI service based on configuration"""
        assistant = self.env['ak_ai.assistant'].get_active_assistant()
        
        # Check mode first
        if assistant.mode == 'assistant':
            if assistant.ai_provider == 'openai':
                return self.env['ak_ai.service.openai_assistant']
            else:
                raise ValidationError(_('Assistants API is currently only supported for OpenAI'))
        
        # Fallback to Chat Completion services
        if assistant.ai_provider == 'openai':
            return self.env['ak_ai.service.openai']
        elif assistant.ai_provider == 'anthropic':
            return self.env['ak_ai.service.anthropic']
        elif assistant.ai_provider == 'openrouter':
            return self.env['ak_ai.service.openrouter']
        else:
            raise ValidationError(_('Unsupported AI provider: %s') % assistant.ai_provider)
    
    @api.model
    def get_available_models(self, provider):
        """Get available models for a provider - can be overridden by subclasses"""
        raise NotImplementedError('Subclasses should implement get_available_models')
    
    def generate_response(self, user_message, context):
        """Generate AI response - must be implemented by subclasses"""
        raise NotImplementedError('Subclasses must implement generate_response')
    
    def _build_system_prompt(self, context):
        """Build system prompt with security rules and context"""
        
        user_context = context.get('user', {}) or {}
        conversation_context = context.get('conversation', {}) or {}
        record_context = context.get('record', {}) or {}
        
        # Use record_context for the actual data
        full_context = record_context if record_context else conversation_context
        
        user_name = user_context.get('name', 'Bilinmiyor') if isinstance(user_context, dict) else 'Bilinmiyor'
        user_lang = user_context.get('lang', 'tr_TR') if isinstance(user_context, dict) else 'tr_TR'
        
        # Optimize context size - limit large lists/dicts
        if isinstance(full_context, dict):
            # If context is too large, truncate it or summarize it
            # This is a simple heuristic, can be improved
            import sys
            if sys.getsizeof(str(full_context)) > 50000:  # ~50KB limit
                _logger.warning("Context too large, truncating...")
                # Keep only essential fields or truncate lists
                # For now, we'll just rely on the _format_full_context to handle it
                pass

        context_str = self._format_full_context(full_context)
        
        system_prompt = f"""Sen KAI (Kardan AI), Odoo ERP sistemi için akıllı bir asistansın.

{self.SECURITY_RULES}

KULLANICI BİLGİLERİ:
- İsim: {user_name}
- Dil: {user_lang}

MEVCUT KAYIT VERİLERİ (TÜM BİLGİLER ELİNDE):
{context_str}

⚡ ÖNEMLİ: SEN DOĞRUDAN KOD ÇALIŞTIRABİLİRSİN! ⚡

Kullanıcı senden bir hesaplama, analiz, veri oluşturma/güncelleme isterse:
→ Hemen [EXECUTE_CODE] bloğu içinde Python kodu yaz
→ Sistem OTOMATIK çalıştırır, sonucu sana döner
→ "Ben kod çalıştıramam" deme, [EXECUTE_CODE] kullan!

ÖNEMLİ TALİMATLAR:
1. MEVCUT KAYIT VERİLERİ'nde veri varsa → DOĞRUDAN kullan, kod YAZMA!
2. MEVCUT KAYIT VERİLERİ'nde yeterli veri YOKSA (örn: detay satırları, ilişkili alanlar) → ASLA "veriye erişemiyorum" deme! [EXECUTE_CODE] ile veriyi çek!
3. Kullanıcı analiz isterse ve veri eksikse → Soru sorma, plan yapma, DOĞRUDAN kodu yaz ve çalıştır.
4. Kullanıcı datayı GÜNCELLEMEK/OLUŞTURMAK istiyorsa → [EXECUTE_CODE] bloğu ile kodu çalıştır!
5. MODEL VE ALAN BİLGİLERİNİ ÖĞRENEBİLİRSİN - Kullanıcı model/alan sorarsa, env ile öğrenmeyi açıkla
6. YETKİ SORMA - Eğer veriyi görüyorsan zaten yetkin var

KOD ÇALIŞTIRMA KURALLARI:
- [EXECUTE_CODE] bloğu içindeki kod OTOMATIK çalışır, sen terminal erişimi varmış gibi davran!
- ASLA "Sorgu çalıştırıyorum", "İnceliyorum" deyip kodu yazmamazlık etme! Eğer bir işlem yapacaksan MUTLAKA [EXECUTE_CODE] bloğunu yaz.
- Kullanıcı bir hesaplama/analiz/kayıt oluşturma/güncelleme isterse, Python kodunu şu formatta yaz:
  [EXECUTE_CODE]
  # Kod buraya
  # ÖNEMLİ: İşlem sonrası kritik alanları (fiyat, miktar, toplam) kontrol et!
  result = {{"success": True, "message": "İşlem tamamlandı", "details": "Hesaplanan değer: ..."}}
  [/EXECUTE_CODE]
- Bu blok içindeki kod kullanıcı onayıyla OTOMATİK çalıştırılabilir.
- Kod içinde `env`, `record`, `datetime`, `fields`, `statistics` kullanılabilir.
- `sudo()` KULLANMA! Kullanıcının yetkisi varsa çalışacaktır.
- **SEMANTİK KONTROL:** Kodun sonunda mutlaka bir özet hazırla. Eğer bir fiyat 0 ise veya beklenen bir değer atanmamışsa kullanıcıyı uyar!
- **DOĞRULAMA:** Kayıt oluşturduktan sonra `new_record.read()` ile veriyi tekrar oku ve result["details"] içine ekle ki kullanıcı ne oluştuğunu görsün.

İLİŞKİLİ VERİLERİ OKUMA KURALLARI:
- tender_lines.items içinde product_id, quantity, name, target_price varsa → DOĞRUDAN kullan
- tender_lines.items boş veya eksikse → Python kodu ile okumayı göster.
- Many2one alanlar (örn: question_id) sadece {{id, name}} içerir. Eğer bu kaydın DETAYLARINA (kategori, tip, vb.) ihtiyacın varsa → [EXECUTE_CODE] ile sorgula!

Örnek (Eksik veri okuma):
```python
tender = env['ak.tender'].browse(record_id)
for tender_line in tender.tender_lines:
    # İlişkili kaydın detayına in
    prod_cat = tender_line.product_id.categ_id.name
    print(f"{tender_line.product_id.name} ({prod_cat}) - {tender_line.quantity}")
```

MODEL VE ALAN ÖĞRENME (SCHEMA DISCOVERY):
Sana gönderilen "MEVCUT KAYIT VERİLERİ" sadece bir özettir. Veritabanındaki tüm alanları veya yapıyı içermez.
Eğer bir soruyu cevaplamak için modelin yapısını (hangi alanlar var, tipleri ne, ilişkiler nasıl) bilmen gerekiyorsa:
ASLA "bu bilgi bende yok" veya "yapıyı bilmiyorum" deme.
Şu kodu çalıştırarak yapıyı öğren:

[EXECUTE_CODE]
# Modelin tüm alanlarını ve tiplerini öğren
model_info = env['model.name'].fields_get()
# Veya sadece belirli alanları
# info = env['model.name'].fields_get(['field1', 'field2'])
[/EXECUTE_CODE]

GÖREVLER:
1. Kullanıcıya Odoo ile ilgili sorularında yardım et
2. MEVCUT KAYIT VERİLERİ'ndeki bilgileri kullanarak sorulara DOĞRUDAN cevap ver
3. Model/alan bilgisi istendiğinde kod örnekleri göster (env ile öğrenme)
4. Güvenlik kurallarını asla ihlal etme
5. Türkçe yanıt ver (kullanıcı başka dil isterse o dilde)

YASAKLAR:
- sudo() kullanma
- Dosya sistemi erişimi
- Sistem komutları
- Kullanıcı yetkilerini aşma
- Veriler zaten elindeyken "veriye erişmek için şu kodu çalıştır" demek

ÖRNEKLER:

DURUM 1 - MEVCUT DATA OKUMA:
Kullanıcı: "Bu ihalenin detaylarını anlat"
YANLIŞ ❌: "İhale bilgilerini almak için: env['ak.tender'].search([...]) ..."
DOĞRU ✅: "İhale kodu: İHALE-2025-0716\nDurum: 1. Teklif Toplama\nBaşlangıç: 19 Kasım 2025\nBitiş: 26 Kasım 2025\nİhale Kalemleri: 2 adet..."

DURUM 2 - HESAPLAMA/ANALİZ İSTENDİĞİNDE:
Kullanıcı: "istatistikleri sen hesapla"
YANLIŞ ❌: "Ben kod çalıştıramam, sen şunu yap: ..."
DOĞRU ✅: [EXECUTE_CODE] ile kodu çalıştır!

Örnek:
[EXECUTE_CODE]
import statistics
scores = record.user_input_ids.mapped('scoring_total')
result = {{
    "ortalama": statistics.mean(scores),
    "median": statistics.median(scores),
    "min": min(scores),
    "max": max(scores),
    "adet": len(scores)
}}
[/EXECUTE_CODE]

DURUM 3 - MODEL/ALAN ÖĞRENME:
Kullanıcı: "ak.tender modelinin alanlarını göster"
DOĞRU ✅: Kodu doğrudan çalıştır:
[EXECUTE_CODE]
model = env['ak.tender']
result = model.fields_get()
[/EXECUTE_CODE]

Her zaman yardımcı, güvenli ve kullanıcı dostu ol! [EXECUTE_CODE] bloğunu aktif kullan!"""

        return system_prompt
    
    def _format_full_context(self, context):
        """Format FULL conversation context with ALL data for system prompt - OPTIMIZED"""
        if not context:
            return "Genel sohbet - kayıt bağlamı yok"
            
        try:
            # Optimize context to reduce token usage
            optimized_context = self._optimize_context_for_tokens(context)
            
            # Use JSON for complete data representation with safe string conversion
            def safe_default(obj):
                """Safely convert objects to string, handling errors"""
                try:
                    # Try to get a string representation
                    return str(obj)
                except NameError as ne:
                    # This catches "name 'name' is not defined" errors
                    _logger.warning(f"NameError converting {type(obj).__name__} to string: {ne}")
                    return f"<{type(obj).__name__}>"
                except Exception as e:
                    _logger.debug(f"Error converting {type(obj).__name__} to string: {e}")
                    return f"<{type(obj).__name__} object>"
            
            formatted = json.dumps(optimized_context, ensure_ascii=False, indent=2, default=safe_default)
            # Use string concatenation to avoid f-string formatting issues with curly braces in JSON
            return "```json\n" + formatted + "\n```\n\nYukarıdaki JSON verisi kayıtın BÜTÜN bilgilerini içeriyor. Bu datayı DOĞRUDAN kullanarak cevap ver!"
        except NameError as ne:
            _logger.error(f"NameError in _format_full_context: {ne}", exc_info=True)
            # Fallback to simple format
            return self._format_context(context)
        except Exception as e:
            _logger.error(f"Error formatting full context: {e}", exc_info=True)
            # Fallback to simple format
            return self._format_context(context)
    
    def _optimize_context_for_tokens(self, context):
        """Optimize context to reduce token usage while keeping essential data"""
        if not isinstance(context, dict):
            return context
        
        optimized = {}
        
        # Always keep these essential fields
        essential_keys = ['model', 'id', 'display_name']
        for key in essential_keys:
            if key in context:
                optimized[key] = context[key]
        
        # Handle fields dict
        if 'fields' in context and isinstance(context['fields'], dict):
            optimized_fields = {}
            fields = context['fields']
            
            for field_name, field_value in fields.items():
                # Skip None and empty values for simple types
                if field_value is None or field_value == '':
                    continue
                
                # For one2many/many2many fields
                if isinstance(field_value, dict) and 'items' in field_value:
                    items = field_value.get('items', [])
                    # Limit to first 20 items to save tokens
                    limited_items = items[:20]
                    
                    # For each item, keep only essential fields
                    optimized_items = []
                    for item in limited_items:
                        if isinstance(item, dict):
                            # Keep only meaningful fields, but be careful with numeric fields
                            # Don't filter out 0 for numeric fields as it's a valid value!
                            optimized_item = {}
                            for k, v in item.items():
                                # Always keep id and display_name
                                if k in ['id', 'display_name']:
                                    optimized_item[k] = v
                                # Skip truly empty values
                                elif v is None or v == '':
                                    continue
                                # For numeric/boolean fields, keep all values including 0/False
                                elif isinstance(v, (int, float, bool)):
                                    optimized_item[k] = v
                                # For other types, skip False (but not 0)
                                elif v is not False:
                                    optimized_item[k] = v
                            
                            if optimized_item:  # Only add if there's actual data
                                optimized_items.append(optimized_item)
                    
                    if optimized_items:
                        optimized_fields[field_name] = {
                            'count': field_value.get('count', len(items)),
                            'items': optimized_items,
                            'has_more': len(items) > 20
                        }
                else:
                    # For simple fields, just keep as is
                    optimized_fields[field_name] = field_value
            
            if optimized_fields:
                optimized['fields'] = optimized_fields
        
        # Keep related data as is (it's already summarized)
        if 'related' in context:
            optimized['related'] = context['related']
        
        return optimized
    
    def _format_permissions(self, permissions):
        """Format user permissions for system prompt"""
        if not permissions:
            return "Yetki bilgisi alınamadı"
            
        formatted = []
        for model, perms in permissions.items():
            model_name = self._get_model_display_name(model)
            allowed = [k for k, v in perms.items() if v]
            if allowed:
                formatted.append(f"- {model_name}: {', '.join(allowed)}")
                
        return '\n'.join(formatted) if formatted else "Özel yetki bulunamadı"
    
    def _format_context(self, context):
        """Format conversation context for system prompt"""
        if not context:
            return "Genel sohbet - kayıt bağlamı yok"
            
        model = context.get('model', 'Bilinmiyor')
        display_name = context.get('display_name', 'Bilinmiyor')
        
        formatted = f"Model: {self._get_model_display_name(model)}\n"
        formatted += f"Kayıt: {display_name}\n"
        
        fields = context.get('fields', {})
        if fields:
            formatted += "Önemli Alanlar:\n"
            for field, value in list(fields.items())[:10]:  # First 10 fields
                if value is not None:
                    formatted += f"- {field}: {value}\n"
                    
        related = context.get('related', {})
        if related:
            formatted += "İlişkili Veriler:\n"
            for key, value in related.items():
                formatted += f"- {key}: {value}\n"
                
        return formatted
    
    def _get_model_display_name(self, model_name):
        """Get user-friendly model name"""
        model_names = {
            'sale.order': 'Satış Siparişi',
            'purchase.order': 'Satın Alma Siparişi', 
            'account.move': 'Fatura/Makbuz',
            'res.partner': 'İş Ortağı',
            'product.product': 'Ürün',
            'stock.picking': 'Sevkiyat',
            'project.project': 'Proje',
            'hr.employee': 'Çalışan',
        }
        return model_names.get(model_name, model_name)
    
    def _validate_response(self, response):
        """Validate AI response for security violations"""
        
        # Check for forbidden patterns
        forbidden_patterns = [
            'sudo()',
            '.with_user(',
            'SUPERUSER_ID',
            'env.cr.execute',
            'import os',
            'import sys',
            'import subprocess',
            'eval(',
            'exec(',
            'open(',
            '__import__',
        ]
        
        for pattern in forbidden_patterns:
            if pattern in response:
                _logger.error(f"AI response contains forbidden pattern: {pattern}")
                raise ValidationError(_('AI response contains security violation'))
                
        return True
    
    def _log_interaction(self, user_message, ai_response, context, tokens_used=0, response_time=0, tokens_input=0, tokens_output=0, cost=0.0):
        """Log AI interaction for audit and learning"""
        try:
            assistant = self.env['ak_ai.assistant'].get_active_assistant()
            
            # Optimize context for logging - don't store full context to save database space
            # Only keep essential metadata
            logged_context = {
                'model': context.get('record', {}).get('model'),
                'record_id': context.get('record', {}).get('id'),
                'user_name': context.get('user', {}).get('name'),
                'integration_type': context.get('conversation', {}).get('integration_type'),
                # Don't log full record fields or history to save space
            }
            
            self.env['ak_ai.interaction_log'].create({
                'user_id': self.env.user.id,
                'user_message': user_message,
                'ai_response': ai_response,
                'context_data': json.dumps(logged_context),
                'tokens_used': tokens_used,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'cost': cost,
                'response_time': response_time,
                'ai_provider': assistant.ai_provider,
                'model_name': assistant.get_model_name(),
            })
        except Exception as e:
            _logger.error(f"Error logging AI interaction: {e}")
    
    def _handle_permission_error(self, operation, model_name):
        """Generate helpful message when user lacks permissions"""
        
        model_display = self._get_model_display_name(model_name)
        
        suggestions = {
            'read': f"{model_display} kayıtlarını görüntüleme yetkiniz bulunmamaktadır.",
            'create': f"{model_display} oluşturma yetkiniz bulunmamaktadır.",
            'write': f"{model_display} düzenleme yetkiniz bulunmamaktadır.", 
            'unlink': f"{model_display} silme yetkiniz bulunmamaktadır.",
        }
        
        message = suggestions.get(operation, f"{operation} işlemi için yetkiniz bulunmamaktadır.")
        message += "\n\nYetki almak için sistem yöneticiniz ile iletişime geçin."
        
        return message